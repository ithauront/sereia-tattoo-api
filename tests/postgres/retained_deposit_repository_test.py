from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from alembic import command
from app.core.config import settings
from app.core.types.payment_enums import PaymentAllocationStatus, PaymentPurposeType
from app.core.types.refund_enums import RefundMethodType, RefundStatus
from app.core.types.refund_filter_types import RefundFilters
from app.infrastructure.sqlalchemy.repositories.payments_repository_sqlalchemy import (
    SQLAlchemyPaymentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.refunds_repository_sqlalchemy import (
    SQLAlchemyRefundsRepository,
)


@pytest.fixture(scope="module")
def engine():
    # Isolate migration tests from the public schema and other PostgreSQL tests.
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
        raise RuntimeError("This test requires a PostgreSQL test database")
    schema = f"migration_test_{uuid4().hex}"
    admin_engine = create_engine(url)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    test_url = url.update_query_dict({"options": f"-csearch_path={schema}"})
    previous_url = settings.DATABASE_URL
    test_engine = create_engine(test_url)
    try:
        settings.DATABASE_URL = test_url.render_as_string(hide_password=False)
        command.upgrade(Config("alembic.ini"), "head")
        yield test_engine
    finally:
        settings.DATABASE_URL = previous_url
        test_engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


def test_initial_migration_round_trip_matches_models(engine):
    config = Config("alembic.ini")
    command.check(config)
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    assert inspect(engine).get_enums() == []
    command.upgrade(config, "head")
    command.check(config)
    columns = {column["name"] for column in inspect(engine).get_columns("payments")}
    assert {"allocation_status", "allocation_changed_at", "allocation_change_reason"} <= columns


@pytest.fixture
def sqlalchemy_payments_repo(db_session):
    return SQLAlchemyPaymentsRepository(db_session)


@pytest.fixture
def sqlalchemy_refunds_repo(db_session):
    return SQLAlchemyRefundsRepository(db_session)


@pytest.mark.parametrize(
    ("refund_status", "method"),
    [
        (RefundStatus.COMPLETED, "sum_completed_by_payable_payments_for_appointment"),
        (RefundStatus.PENDING, "sum_pending_by_payable_payments_for_appointment"),
    ],
)
def test_retention_excludes_deposit_and_its_refund_but_preserves_history(
    sqlalchemy_payments_repo,
    sqlalchemy_refunds_repo,
    refund_status,
    method,
    sqlalchemy_users_repo,
    sqlalchemy_appointments_repo,
    db_session,
    make_user,
    make_quoted_appointment,
    make_payment,
    make_refund,
):
    payments, refunds = sqlalchemy_payments_repo, sqlalchemy_refunds_repo
    user = make_user()
    sqlalchemy_users_repo.create(user)
    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)
    deposit = make_payment(
        appointment_id=appointment.id,
        vip_client_id=None,
        payment_purpose=PaymentPurposeType.DEPOSIT,
        amount=Decimal("50"),
    )
    payments.create(deposit)
    refund = make_refund(
        payment_id=deposit.id,
        appointment_id=appointment.id,
        vip_client_id=None,
        refund_method=RefundMethodType.PIX,
        refund_status=refund_status,
        created_by_user_id=user.id,
        amount=Decimal("50"),
    )
    refunds.create(refund)
    sum_refunds = getattr(refunds, method)
    assert sum_refunds(appointment.id) == Decimal("50")
    assert payments.sum_payable_by_appointment_id(appointment.id) == Decimal("50")

    retained_at = datetime(2026, 1, 2, 10, tzinfo=timezone.utc)
    deposit.retain_deposit(reason="Reagendamento fora do prazo", retained_at=retained_at)
    payments.update_allocation_status(payment=deposit)
    db_session.flush()
    db_session.expire_all()

    assert payments.sum_payable_by_appointment_id(appointment.id) == Decimal("0")
    assert sum_refunds(appointment.id) == Decimal("0")
    persisted = payments.find_by_id(deposit.id)
    assert persisted is not None
    assert persisted.payment_purpose == PaymentPurposeType.DEPOSIT
    assert persisted.amount == Decimal("50")
    assert persisted.allocation_status == PaymentAllocationStatus.RETAINED
    assert persisted.allocation_changed_at == retained_at
    assert persisted.allocation_change_reason == "Reagendamento fora do prazo"
    assert refunds.find_by_id(refund.id) is not None
    assert refunds.sum_amount(filters=RefundFilters(appointment_id=appointment.id)) == Decimal("50")

    # An active payment and its refund must still participate in the balance.
    active = make_payment(appointment_id=appointment.id, vip_client_id=None, amount=Decimal("200"))
    payments.create(active)
    refunds.create(
        make_refund(
            payment_id=active.id,
            appointment_id=appointment.id,
            vip_client_id=None,
            refund_method=RefundMethodType.PIX,
            refund_status=refund_status,
            created_by_user_id=user.id,
            amount=Decimal("20"),
        )
    )
    assert payments.sum_payable_by_appointment_id(appointment.id) == Decimal("200")
    assert sum_refunds(appointment.id) == Decimal("20")
