from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.application.studio.use_cases.DTO.commun import Direction
from app.core.types.payment_enums import PaymentPurposeType
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


@pytest.mark.parametrize(
    ("repository_method", "included_status", "excluded_status"),
    [
        (
            "sum_completed_by_payable_payments_for_appointment",
            RefundStatus.COMPLETED,
            RefundStatus.PENDING,
        ),
        (
            "sum_pending_by_payable_payments_for_appointment",
            RefundStatus.PENDING,
            RefundStatus.COMPLETED,
        ),
    ],
)
def test_sum_refunds_only_for_payable_payments_of_same_appointment_and_status(
    repository_method,
    included_status,
    excluded_status,
    sqlalchemy_refunds_repo: SQLAlchemyRefundsRepository,
    sqlalchemy_payments_repo: SQLAlchemyPaymentsRepository,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_refund,
    make_payment,
    make_quoted_appointment,
    make_user,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)
    appointment = make_quoted_appointment(user_id=user.id)
    other_appointment = make_quoted_appointment(user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)
    sqlalchemy_appointments_repo.create(other_appointment)

    def create_payment(*, purpose, linked_appointment):
        payment = make_payment(
            appointment_id=linked_appointment.id,
            vip_client_id=None,
            payment_purpose=purpose,
        )
        sqlalchemy_payments_repo.create(payment)
        return payment

    appointment_payment = create_payment(
        purpose=PaymentPurposeType.APPOINTMENT,
        linked_appointment=appointment,
    )
    deposit_payment = create_payment(
        purpose=PaymentPurposeType.DEPOSIT,
        linked_appointment=appointment,
    )
    tip_payment = create_payment(
        purpose=PaymentPurposeType.TIP,
        linked_appointment=appointment,
    )
    other_purpose_payment = create_payment(
        purpose=PaymentPurposeType.OTHER,
        linked_appointment=appointment,
    )
    other_appointment_payment = create_payment(
        purpose=PaymentPurposeType.APPOINTMENT,
        linked_appointment=other_appointment,
    )

    def create_refund(*, payment, amount, status, linked_appointment=appointment):
        sqlalchemy_refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                appointment_id=linked_appointment.id,
                amount=amount,
                refund_status=status,
                refund_method=RefundMethodType.PIX,
                vip_client_id=None,
                created_by_user_id=user.id,
            )
        )

    create_refund(payment=appointment_payment, amount=Decimal("30"), status=included_status)
    create_refund(payment=deposit_payment, amount=Decimal("10"), status=included_status)
    create_refund(payment=appointment_payment, amount=Decimal("20"), status=excluded_status)
    create_refund(payment=tip_payment, amount=Decimal("100"), status=included_status)
    create_refund(payment=other_purpose_payment, amount=Decimal("100"), status=included_status)
    create_refund(
        payment=other_appointment_payment,
        amount=Decimal("500"),
        status=included_status,
    )
    create_refund(
        payment=appointment_payment,
        amount=Decimal("500"),
        status=included_status,
        linked_appointment=other_appointment,
    )

    total = getattr(sqlalchemy_refunds_repo, repository_method)(appointment_id=appointment.id)

    assert total == Decimal("40")


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
