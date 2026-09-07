from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import StaticPool, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.application.event_bus.transactional_event_bus import TransactionalEventBus
from app.application.studio.handlers.confirm_deposit import ConfirmDepositHandler
from app.application.studio.use_cases.DTO.payment_dto import CreatePaymentInput
from app.application.studio.use_cases.finances_use_cases.create_payment_use_case import (
    CreatePaymentUseCase,
)
from app.core.exceptions.appointments import (
    AppointmentClientInfoBreakingDomainRules,
    IncorrectAppointmentStatusError,
)
from app.core.types.appointment_enums import AppointmentStatus
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.core.types.payment_enums import PaymentMethodType, PaymentPurposeType
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.finances.events.deposit_payment_recorded_event import (
    DepositPaymentRecordedEvent,
)
from app.infrastructure.sqlalchemy.base_class import Base
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.audit_logs_repository import (
    SQLAlchemyAuditLogsRepository,
)
from app.infrastructure.sqlalchemy.repositories.client_credit_entries_repository import (
    SQLAlchemyClientCreditEntriesRepository,
)
from app.infrastructure.sqlalchemy.repositories.payments_repository_sqlalchemy import (
    SQLAlchemyPaymentsRepository,
)
from app.infrastructure.sqlalchemy.unit_of_work.write_unit_of_work import (
    SqlAlchemyWriteUnitOfWork,
)


@pytest.fixture
def payment_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, future=True)

    yield session_factory

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def persist_payment_dependencies(
    *,
    session_factory,
    actor,
    vip_client,
    appointment,
    initial_credit,
):
    uow = SqlAlchemyWriteUnitOfWork(session=session_factory())
    with uow:
        uow.users.create(actor)
        uow.vip_clients.create(vip_client)
        uow.appointments.create(appointment)
        uow.client_credit_entries.create(initial_credit)


def make_credit_payment_input(*, actor, vip_client, appointment, payment_id):
    return CreatePaymentInput(
        idempotency_key=payment_id,
        actor=actor,
        amount=Decimal("10.99"),
        payment_method=PaymentMethodType.CLIENT_CREDIT,
        payment_purpose=PaymentPurposeType.APPOINTMENT,
        appointment_id=appointment.id,
        credit_owner_vip_client_id=vip_client.id,
        description="pagamento integrado com créditos",
    )


async def test_create_client_credit_payment_persists_payment_debit_and_audits(
    payment_session_factory,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_entry,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    vip_client = make_vip_client()
    appointment = make_quoted_appointment(user_id=actor.id)
    initial_credit = make_client_credit_entry(vip_client_id=vip_client.id, quantity=10)
    persist_payment_dependencies(
        session_factory=payment_session_factory,
        actor=actor,
        vip_client=vip_client,
        appointment=appointment,
        initial_credit=initial_credit,
    )
    data = make_credit_payment_input(
        actor=actor,
        vip_client=vip_client,
        appointment=appointment,
        payment_id=uuid4(),
    )

    await CreatePaymentUseCase(
        SqlAlchemyWriteUnitOfWork(session=payment_session_factory()),
        fake_transactional_event_bus,
        fake_integration_event_bus,
    ).execute(data)

    session: Session = payment_session_factory()
    payments = SQLAlchemyPaymentsRepository(session)
    credits = SQLAlchemyClientCreditEntriesRepository(session)
    audits = SQLAlchemyAuditLogsRepository(session)
    payment = payments.find_by_id(data.idempotency_key)
    debit_entries = credits.find_many_by_source_id(source_id=data.idempotency_key)

    assert payment is not None
    assert payment.amount == Decimal("10.99")
    assert len(debit_entries) == 1
    assert debit_entries[0].source_type == ClientCreditSourceType.USED_AS_PAYMENT
    assert debit_entries[0].quantity == -10
    assert credits.get_balance(vip_client_id=vip_client.id) == 0
    assert len(audits.find_many_by_entity_name(entity_name="payments")) == 1
    assert len(audits.find_many_by_entity_name(entity_name="client_credit_entry")) == 1
    session.close()


class FailingAuditLogsRepository:
    def create(self, _audit_log):
        raise RuntimeError("audit persistence failed")


class FailingDepositHandler:
    async def handle(self, _event, *, uow):
        raise RuntimeError("deposit confirmation failed")


async def test_failure_after_flush_rolls_back_payment_and_credit_debit(
    payment_session_factory,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_entry,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    vip_client = make_vip_client()
    appointment = make_quoted_appointment(user_id=actor.id)
    initial_credit = make_client_credit_entry(vip_client_id=vip_client.id, quantity=10)
    persist_payment_dependencies(
        session_factory=payment_session_factory,
        actor=actor,
        vip_client=vip_client,
        appointment=appointment,
        initial_credit=initial_credit,
    )
    data = make_credit_payment_input(
        actor=actor,
        vip_client=vip_client,
        appointment=appointment,
        payment_id=uuid4(),
    )
    uow = SqlAlchemyWriteUnitOfWork(session=payment_session_factory())
    uow.audit_logs = FailingAuditLogsRepository()

    with pytest.raises(RuntimeError, match="audit persistence failed"):
        await CreatePaymentUseCase(
            uow, fake_transactional_event_bus, fake_integration_event_bus
        ).execute(data)

    session: Session = payment_session_factory()
    payments = SQLAlchemyPaymentsRepository(session)
    credits = SQLAlchemyClientCreditEntriesRepository(session)
    assert payments.find_by_id(data.idempotency_key) is None
    assert credits.find_many_by_source_id(source_id=data.idempotency_key) == []
    assert credits.get_balance(vip_client_id=vip_client.id) == 10
    session.close()


async def test_deposit_payment_confirms_appointment_in_same_flow(
    payment_session_factory,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_entry,
    fake_integration_event_bus,
):
    actor = make_user()
    vip_client = make_vip_client()
    appointment = make_quoted_appointment(user_id=actor.id)
    initial_credit = make_client_credit_entry(vip_client_id=vip_client.id, quantity=10)
    persist_payment_dependencies(
        session_factory=payment_session_factory,
        actor=actor,
        vip_client=vip_client,
        appointment=appointment,
        initial_credit=initial_credit,
    )
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        appointment_id=appointment.id,
        description="caução",
    )
    transactional_bus = TransactionalEventBus()
    transactional_bus.register(DepositPaymentRecordedEvent, ConfirmDepositHandler())

    await CreatePaymentUseCase(
        SqlAlchemyWriteUnitOfWork(session=payment_session_factory()),
        transactional_bus,
        fake_integration_event_bus,
    ).execute(data)

    session: Session = payment_session_factory()
    persisted_appointment = SQLAlchemyAppointmentsRepository(session).find_by_id(appointment.id)
    assert persisted_appointment is not None
    assert persisted_appointment.status == AppointmentStatus.SCHEDULED
    assert persisted_appointment.deposit_confirmed_at is not None
    assert len(fake_integration_event_bus.events) == 1
    assert fake_integration_event_bus.events[0].client_email == appointment.client_info.email
    session.close()


async def test_deposit_handler_failure_rolls_back_payment_and_does_not_request_email(
    payment_session_factory,
    make_user,
    make_vip_client,
    make_quoted_appointment,
    make_client_credit_entry,
    fake_integration_event_bus,
):
    actor = make_user()
    vip_client = make_vip_client()
    appointment = make_quoted_appointment(user_id=actor.id)
    initial_credit = make_client_credit_entry(vip_client_id=vip_client.id, quantity=10)
    persist_payment_dependencies(
        session_factory=payment_session_factory,
        actor=actor,
        vip_client=vip_client,
        appointment=appointment,
        initial_credit=initial_credit,
    )
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("10"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        appointment_id=appointment.id,
        description="caução",
    )
    transactional_bus = TransactionalEventBus()
    transactional_bus.register(DepositPaymentRecordedEvent, FailingDepositHandler())

    with pytest.raises(RuntimeError, match="deposit confirmation failed"):
        await CreatePaymentUseCase(
            SqlAlchemyWriteUnitOfWork(session=payment_session_factory()),
            transactional_bus,
            fake_integration_event_bus,
        ).execute(data)

    session: Session = payment_session_factory()
    persisted_payment = SQLAlchemyPaymentsRepository(session).find_by_id(data.idempotency_key)
    persisted_appointment = SQLAlchemyAppointmentsRepository(session).find_by_id(appointment.id)
    assert persisted_payment is None
    assert persisted_appointment is not None
    assert persisted_appointment.status == AppointmentStatus.QUOTED
    assert persisted_appointment.deposit_confirmed_at is None
    assert fake_integration_event_bus.events == []
    session.close()


async def test_invalid_deposit_status_rolls_back_payment_and_audit(
    payment_session_factory,
    make_user,
    make_scheduled_appointment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    appointment = make_scheduled_appointment(user_id=actor.id)
    with SqlAlchemyWriteUnitOfWork(session=payment_session_factory()) as setup_uow:
        setup_uow.users.create(actor)
        setup_uow.appointments.create(appointment)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("50"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        appointment_id=appointment.id,
        description="caução inválida",
    )

    with pytest.raises(IncorrectAppointmentStatusError):
        await CreatePaymentUseCase(
            SqlAlchemyWriteUnitOfWork(session=payment_session_factory()),
            fake_transactional_event_bus,
            fake_integration_event_bus,
        ).execute(data)

    session: Session = payment_session_factory()
    assert SQLAlchemyPaymentsRepository(session).find_by_id(data.idempotency_key) is None
    assert SQLAlchemyAuditLogsRepository(session).find_many_by_entity_id(data.idempotency_key) == []
    assert fake_transactional_event_bus.events == []
    assert fake_integration_event_bus.events == []
    session.close()


async def test_missing_appointment_vip_rolls_back_payment_and_audit(
    payment_session_factory,
    make_user,
    make_quoted_appointment,
    fake_transactional_event_bus,
    fake_integration_event_bus,
):
    actor = make_user()
    appointment = make_quoted_appointment(
        user_id=actor.id,
        client_info=ClientInfo(vip_client_id=uuid4()),
    )
    with SqlAlchemyWriteUnitOfWork(session=payment_session_factory()) as setup_uow:
        setup_uow.users.create(actor)
        setup_uow.appointments.create(appointment)
    data = CreatePaymentInput(
        idempotency_key=uuid4(),
        actor=actor,
        amount=Decimal("50"),
        payment_method=PaymentMethodType.PIX,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        appointment_id=appointment.id,
        description="caução",
    )

    with pytest.raises(AppointmentClientInfoBreakingDomainRules):
        await CreatePaymentUseCase(
            SqlAlchemyWriteUnitOfWork(session=payment_session_factory()),
            fake_transactional_event_bus,
            fake_integration_event_bus,
        ).execute(data)

    session: Session = payment_session_factory()
    assert SQLAlchemyPaymentsRepository(session).find_by_id(data.idempotency_key) is None
    assert SQLAlchemyAuditLogsRepository(session).find_many_by_entity_id(data.idempotency_key) == []
    assert fake_integration_event_bus.events == []
    session.close()
