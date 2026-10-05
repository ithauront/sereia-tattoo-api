from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.application.studio.use_cases.appointments_use_cases import reschedule_appointment_use_case
from app.application.studio.use_cases.appointments_use_cases.reschedule_appointment_use_case import (
    RescheduleAppointmentUseCase,
)
from app.application.studio.use_cases.DTO.reschedule_appointment_dto import RescheduleAppointmentInput
from app.core.config import settings
from app.core.types.appointment_enums import AppointmentStatus
from app.core.types.payment_enums import PaymentAllocationStatus, PaymentPurposeType
from app.domain.studio.appointments.policies.appointment_authorization_policy import (
    AppointmentAuthorizationPolicy,
)
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)
from app.domain.studio.appointments.policies.deposit_policy import DepositPolicy
from app.infrastructure.sqlalchemy.base import Base
from app.infrastructure.sqlalchemy.unit_of_work.read_unit_of_work import SqlAlchemyReadUnitOfWork
from app.infrastructure.sqlalchemy.unit_of_work.write_unit_of_work import SqlAlchemyWriteUnitOfWork
from tests.fakes.fake_event_bus import FakeIntegrationEventBus

NOW = datetime(2035, 1, 1, 9, tzinfo=timezone.utc)

# TODO(reschedule): testar duas sessões concorrentes disputando o mesmo horário e
# reschedule concorrente com cancel/complete/pagamento, após implementar a proteção.
# Verificar que a transação rejeitada não persiste retenção/auditoria nem publica evento.


@pytest.fixture(scope="module")
def transaction_engine():
    # Isolate committed data without the outer transaction used by db_session fixtures.
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
        raise RuntimeError("This test requires a PostgreSQL test database")
    schema = f"reschedule_test_{uuid4().hex}"
    admin_engine = create_engine(url)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url.update_query_dict({"options": f"-csearch_path={schema}"}))
    try:
        Base.metadata.create_all(engine)
        yield engine
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


@pytest.fixture
def scenario(
    transaction_engine,
    monkeypatch,
    make_user,
    make_scheduled_appointment,
    make_calendar_settings,
    make_payment,
):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW.astimezone(tz) if tz else NOW.replace(tzinfo=None)

    monkeypatch.setattr(reschedule_appointment_use_case, "datetime", Clock)
    owner = make_user(username=f"u{uuid4().hex[:20]}", email=f"{uuid4().hex}@example.com")
    appointment = make_scheduled_appointment(
        user_id=owner.id,
        start_at=NOW + timedelta(days=1),
        end_at=NOW + timedelta(days=1, hours=1),
    )
    payment = make_payment(
        appointment_id=appointment.id,
        vip_client_id=None,
        payment_purpose=PaymentPurposeType.DEPOSIT,
    )
    # Commit the initial state so a later rollback cannot merely erase the setup.
    with SqlAlchemyWriteUnitOfWork(Session(transaction_engine)) as setup:
        setup.users.create(owner)
        setup.appointments.create(appointment)
        setup.calendar_settings.create(make_calendar_settings(user_id=owner.id))
        setup.payments.create(payment)

    with Session(transaction_engine) as write_session, Session(transaction_engine) as read_session:
        uow = SqlAlchemyWriteUnitOfWork(write_session)
        bus = FakeIntegrationEventBus()
        use_case = RescheduleAppointmentUseCase(
            write_uow=uow,
            read_uow=SqlAlchemyReadUnitOfWork(read_session),
            calendar_policy=CalendarAvailabilityPolicy(),
            deposit_policy=DepositPolicy(),
            authorization_policy=AppointmentAuthorizationPolicy(),
            integration_bus=bus,
        )
        yield SimpleNamespace(
            bus=bus,
            uow=uow,
            use_case=use_case,
            appointment=appointment,
            payment=payment,
            engine=transaction_engine,
            data=RescheduleAppointmentInput(
                appointment_id=appointment.id,
                actor=owner,
                start_at=NOW + timedelta(days=7),
                end_at=NOW + timedelta(days=7, hours=1),
            ),
        )


def assert_original_state(s, reader):
    appointment = reader.appointments.find_by_id(s.appointment.id)
    payment = reader.payments.find_by_id(s.payment.id)
    assert appointment.start_at == s.appointment.start_at
    assert appointment.end_at == s.appointment.end_at
    assert appointment.status == AppointmentStatus.SCHEDULED
    assert appointment.deposit_confirmed_at == s.appointment.deposit_confirmed_at
    assert appointment.observations == s.appointment.observations
    assert payment.allocation_status == PaymentAllocationStatus.ACTIVE
    assert payment.allocation_changed_at is None
    assert payment.allocation_change_reason is None
    assert reader.audit_logs.find_many_by_entity_id(s.appointment.id) == []


async def test_reschedule_commits_appointment_payment_and_audit_together(scenario, monkeypatch):
    s = scenario
    original_publish = s.bus.publish

    async def publish_after_commit(event, **context):
        # Verifique o banco durante a publicação, não apenas depois de execute retornar.
        with Session(s.engine) as observer:
            reader = SqlAlchemyReadUnitOfWork(observer)
            assert reader.appointments.find_by_id(s.appointment.id).start_at == event.start_at
            assert (
                reader.payments.find_by_id(s.payment.id).allocation_status
                == PaymentAllocationStatus.RETAINED
            )
            assert len(reader.audit_logs.find_many_by_entity_id(s.appointment.id)) == 1
        await original_publish(event, **context)

    monkeypatch.setattr(s.bus, "publish", publish_after_commit)
    await s.use_case.execute(s.data)
    assert len(s.bus.events) == 1

    # A new session proves persistence beyond the UoW's identity map/transaction.
    with Session(s.engine) as session:
        reader = SqlAlchemyReadUnitOfWork(session)
        appointment = reader.appointments.find_by_id(s.appointment.id)
        payment = reader.payments.find_by_id(s.payment.id)
        logs = reader.audit_logs.find_many_by_entity_id(s.appointment.id)
        assert appointment.start_at == s.data.start_at
        assert appointment.end_at == s.data.end_at
        assert appointment.status == AppointmentStatus.QUOTED
        assert appointment.deposit_confirmed_at is None
        assert payment.allocation_status == PaymentAllocationStatus.RETAINED
        assert payment.payment_purpose == PaymentPurposeType.DEPOSIT
        assert payment.amount == s.payment.amount
        assert payment.allocation_changed_at == NOW
        assert payment.allocation_change_reason
        assert len(logs) == 1
        assert logs[0].actor_id == s.data.actor.id
        assert logs[0].changes["retained_payment_ids"] == [str(payment.id)]
        assert logs[0].changes["was_deposit_retained"] is True


@pytest.mark.parametrize("after_audit_insert", [False, True])
async def test_reschedule_rolls_back_flushed_changes_on_audit_failure(
    scenario,
    monkeypatch,
    after_audit_insert,
):
    s = scenario
    create_audit = s.uow.audit_logs.create
    reached_failure = []

    def fail_during_audit(log):
        if after_audit_insert:
            create_audit(log)
        s.uow.session.flush()
        s.uow.session.expire_all()
        # Verify that the UPDATEs reached PostgreSQL before provoking rollback.
        appointment = s.uow.appointments.find_by_id(s.appointment.id)
        payment = s.uow.payments.find_by_id(s.payment.id)
        assert appointment.start_at == s.data.start_at
        assert appointment.status == AppointmentStatus.QUOTED
        assert appointment.deposit_confirmed_at is None
        assert payment.allocation_status == PaymentAllocationStatus.RETAINED
        assert len(s.uow.audit_logs.find_many_by_entity_id(appointment.id)) == int(after_audit_insert)
        # Another connection must still see only the previously committed state.
        with Session(s.engine) as observer:
            assert_original_state(s, SqlAlchemyReadUnitOfWork(observer))
        reached_failure.append(True)
        raise RuntimeError("simulated audit failure")

    monkeypatch.setattr(s.uow.audit_logs, "create", fail_during_audit)
    with pytest.raises(RuntimeError, match="simulated audit failure"):
        await s.use_case.execute(s.data)
    assert reached_failure == [True]
    assert s.bus.events == []
    with Session(s.engine) as session:
        assert_original_state(s, SqlAlchemyReadUnitOfWork(session))
