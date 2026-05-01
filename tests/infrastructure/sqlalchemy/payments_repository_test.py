from decimal import Decimal
from sqlalchemy.exc import IntegrityError

import pytest

from app.core.types.payment_enums import PaymentMethodType
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.payments_repository_sqlalchemy import (
    SQLAlchemyPaymentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)


def test_create_and_find_by_id(
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    make_payment,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_vip_client,
    make_quoted_appointment,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment()
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(
        amount=Decimal("10"), appointment_id=appointment.id, vip_client_id=vip_client.id
    )
    sqlalchemy_payments_repo.create(payment)

    result = sqlalchemy_payments_repo.find_by_id(payment.id)

    assert result is not None

    assert result.id == payment.id
    assert result.amount == Decimal("10")


def test_unique_external_reference_constraint(
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    make_payment,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_vip_client,
    make_quoted_appointment,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment()
    sqlalchemy_appointments_repo.create(appointment)

    payment1 = make_payment(
        amount=Decimal("10"),
        appointment_id=appointment.id,
        vip_client_id=vip_client.id,
        external_reference="ref-1",
    )
    payment2 = make_payment(
        amount=Decimal("10"),
        appointment_id=appointment.id,
        vip_client_id=vip_client.id,
        external_reference="ref-1",
    )

    sqlalchemy_payments_repo.create(payment1)

    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_payments_repo.create(payment2)

    assert "UNIQUE constraint failed" in str(exc.value)


def test_null_external_reference_allows_duplicates(
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    make_payment,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_vip_client,
    make_quoted_appointment,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment()
    sqlalchemy_appointments_repo.create(appointment)

    payment1 = make_payment(
        amount=Decimal("10"),
        appointment_id=appointment.id,
        vip_client_id=vip_client.id,
        external_reference=None,
    )
    payment2 = make_payment(
        amount=Decimal("10"),
        appointment_id=appointment.id,
        vip_client_id=vip_client.id,
        external_reference=None,
    )

    sqlalchemy_payments_repo.create(payment1)
    sqlalchemy_payments_repo.create(payment2)

    assert True


def test_amount_precision(
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    make_payment,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_vip_client,
    make_quoted_appointment,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment()
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(
        amount=Decimal("10.55"),
        appointment_id=appointment.id,
        vip_client_id=vip_client.id,
    )

    sqlalchemy_payments_repo.create(payment)

    result = sqlalchemy_payments_repo.find_by_id(payment.id)

    assert result is not None

    assert result.amount == Decimal("10.55")


def test_payment_method_enum_persistence(
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    make_payment,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_vip_client,
    make_quoted_appointment,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment()
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        vip_client_id=vip_client.id,
        payment_method=PaymentMethodType.PIX,
    )

    sqlalchemy_payments_repo.create(payment)

    result = sqlalchemy_payments_repo.find_by_id(payment.id)

    assert result is not None

    assert result.payment_method == PaymentMethodType.PIX


def test_created_at_is_persisted(
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    make_payment,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_vip_client,
    make_quoted_appointment,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment()
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        vip_client_id=vip_client.id,
    )

    sqlalchemy_payments_repo.create(payment)

    result = sqlalchemy_payments_repo.find_by_id(payment.id)

    assert result is not None

    assert result.created_at is not None
