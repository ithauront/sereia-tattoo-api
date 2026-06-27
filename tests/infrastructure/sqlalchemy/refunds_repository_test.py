from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.application.studio.use_cases.DTO.commun import Direction
from app.core.types.refund_enums import RefundMethodType, RefundStatus
from app.core.types.refund_filter_types import RefundFilters
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.payments_repository_sqlalchemy import (
    SQLAlchemyPaymentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.refunds_repository_sqlalchemy import (
    SQLAlchemyRefundsRepository,
)
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)


def test_create_and_find_by_id(
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    make_refund,
    make_payment,
    make_vip_client,
    make_quoted_appointment,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(appointment_id=appointment.id, vip_client_id=vip_client.id)
    sqlalchemy_payments_repo.create(payment)

    refund = make_refund(
        payment_id=payment.id,
        amount=Decimal("20"),
        refund_method=RefundMethodType.PIX,
        vip_client_id=None,
        appointment_id=None,
        created_by_user_id=user.id,
    )
    sqlalchemy_refunds_repo.create(refund)

    result = sqlalchemy_refunds_repo.find_by_id(refund.id)

    assert result is not None

    assert result.id == refund.id
    assert result.amount == Decimal("20")


def test_amount_precision(
    make_payment,
    make_refund,
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    make_vip_client,
    make_quoted_appointment,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(appointment_id=appointment.id, vip_client_id=vip_client.id)
    sqlalchemy_payments_repo.create(payment)

    refund = make_refund(
        payment_id=payment.id,
        amount=Decimal("20.67"),
        refund_method=RefundMethodType.PIX,
        vip_client_id=None,
        appointment_id=None,
        created_by_user_id=user.id,
    )
    sqlalchemy_refunds_repo.create(refund)

    result = sqlalchemy_refunds_repo.find_by_id(refund.id)

    assert result is not None

    assert result.amount == Decimal("20.67")


def test_refund_method_enum_persistence(
    make_payment,
    make_refund,
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    make_vip_client,
    make_quoted_appointment,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(appointment_id=appointment.id, vip_client_id=vip_client.id)
    sqlalchemy_payments_repo.create(payment)

    refund = make_refund(
        payment_id=payment.id,
        refund_method=RefundMethodType.PIX,
        vip_client_id=None,
        appointment_id=None,
        created_by_user_id=user.id,
    )
    sqlalchemy_refunds_repo.create(refund)

    result = sqlalchemy_refunds_repo.find_by_id(refund.id)
    assert result is not None

    assert result.refund_method == RefundMethodType.PIX


def test_refund_status_enum_persistence(
    make_payment,
    make_refund,
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    make_vip_client,
    make_quoted_appointment,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(appointment_id=appointment.id, vip_client_id=vip_client.id)
    sqlalchemy_payments_repo.create(payment)

    refund = make_refund(
        payment_id=payment.id,
        refund_status=RefundStatus.COMPLETED,
        refund_method=RefundMethodType.PIX,
        vip_client_id=None,
        appointment_id=None,
        created_by_user_id=user.id,
    )
    sqlalchemy_refunds_repo.create(refund)

    result = sqlalchemy_refunds_repo.find_by_id(refund.id)
    assert result is not None

    assert result.refund_status == RefundStatus.COMPLETED


def test_created_at_is_persisted(
    make_payment,
    make_refund,
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    make_vip_client,
    make_quoted_appointment,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(appointment_id=appointment.id, vip_client_id=vip_client.id)
    sqlalchemy_payments_repo.create(payment)

    refund = make_refund(
        payment_id=payment.id,
        refund_status=RefundStatus.COMPLETED,
        refund_method=RefundMethodType.PIX,
        vip_client_id=None,
        appointment_id=None,
        created_by_user_id=user.id,
    )
    sqlalchemy_refunds_repo.create(refund)

    result = sqlalchemy_refunds_repo.find_by_id(refund.id)

    assert result is not None

    assert result.created_at is not None


def test_vip_client_id_is_persisted(
    make_payment,
    make_refund,
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    make_vip_client,
    make_quoted_appointment,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(appointment_id=appointment.id, vip_client_id=vip_client.id)
    sqlalchemy_payments_repo.create(payment)

    refund = make_refund(
        payment_id=payment.id,
        refund_status=RefundStatus.COMPLETED,
        vip_client_id=vip_client.id,
        appointment_id=None,
        created_by_user_id=user.id,
    )
    sqlalchemy_refunds_repo.create(refund)

    result = sqlalchemy_refunds_repo.find_by_id(refund.id)

    assert result is not None
    assert result.vip_client_id == vip_client.id


def test_payment_fk_constraint(
    sqlalchemy_refunds_repo,
    make_refund,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    refund = make_refund(
        payment_id=uuid4(),
        refund_method=RefundMethodType.PIX,
        vip_client_id=None,
        appointment_id=None,
        created_by_user_id=user.id,
    )

    with pytest.raises(IntegrityError):
        sqlalchemy_refunds_repo.create(refund)


def test_appointment_fk_constraint(
    sqlalchemy_refunds_repo,
    make_refund,
):
    refund = make_refund(
        appointment_id=uuid4(),
    )

    with pytest.raises(IntegrityError):
        sqlalchemy_refunds_repo.create(refund)


def test_created_by_user_fk_constraint(
    sqlalchemy_refunds_repo,
    make_refund,
):
    refund = make_refund(
        created_by_user_id=uuid4(),
        refund_method=RefundMethodType.PIX,
        vip_client_id=None,
        appointment_id=None,
    )

    with pytest.raises(IntegrityError):
        sqlalchemy_refunds_repo.create(refund)


def test_find_many_order_asc(
    make_payment,
    make_refund,
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    make_vip_client,
    make_quoted_appointment,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(appointment_id=appointment.id, vip_client_id=vip_client.id)
    sqlalchemy_payments_repo.create(payment)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        sqlalchemy_refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                reason=f"reason {i}",
                created_at=base_now + timedelta(seconds=i),
                refund_method=RefundMethodType.PIX,
                vip_client_id=None,
                appointment_id=None,
                created_by_user_id=user.id,
            )
        )

    founds = sqlalchemy_refunds_repo.find_many(
        filters=RefundFilters(),
        direction=Direction.asc,
    )

    assert [r.reason for r in founds] == [
        "reason 0",
        "reason 1",
        "reason 2",
        "reason 3",
        "reason 4",
    ]


def test_find_many_pagination(
    make_payment,
    make_refund,
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    make_vip_client,
    make_quoted_appointment,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    payment = make_payment(appointment_id=appointment.id, vip_client_id=vip_client.id)
    sqlalchemy_payments_repo.create(payment)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        sqlalchemy_refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                reason=f"reason {i}",
                refund_method=RefundMethodType.PIX,
                created_at=base_now + timedelta(seconds=i),
                vip_client_id=None,
                appointment_id=None,
                created_by_user_id=user.id,
            )
        )

    founds = sqlalchemy_refunds_repo.find_many(
        filters=RefundFilters(),
        limit=2,
        offset=1,
        direction=Direction.desc,
    )

    assert [r.reason for r in founds] == [
        "reason 3",
        "reason 2",
    ]
