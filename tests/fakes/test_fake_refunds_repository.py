from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.application.studio.use_cases.DTO.commun import Direction
from app.core.types.refund_enums import RefundMethodType, RefundStatus
from app.core.types.refund_filter_types import RefundFilters
from app.domain.studio.finances.entities.refund import Refund
from tests.fakes.fake_payments_repository import FakePaymentsRepository
from tests.fakes.fake_refunds_repository import FakeRefundsRepository
from tests.fakes.fake_users_repository import FakeUsersRepository
from tests.fakes.test_fake_appointment_repository import FakeAppointmentsRepository


@pytest.fixture
def payments_repo():
    return FakePaymentsRepository()


@pytest.fixture
def refunds_repo():
    return FakeRefundsRepository()


@pytest.fixture
def appointments_repo():
    return FakeAppointmentsRepository()


@pytest.fixture
def users_repo():
    return FakeUsersRepository()


def test_create_and_find_by_id(make_refund, make_payment, payments_repo, refunds_repo):
    payment = make_payment()
    payments_repo.create(payment)

    refund = make_refund(payment_id=payment.id)
    refunds_repo.create(refund)

    found = refunds_repo.find_by_id(refund.id)

    assert found is not None
    assert isinstance(found, Refund)
    assert found.payment_id == payment.id
    assert found.reason == "Pagamento equivocado com valor superior"


def test_find_many(make_payment, make_refund, payments_repo, refunds_repo):
    payment = make_payment()
    payments_repo.create(payment)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        created_at = base_now + timedelta(seconds=i)
        refund = make_refund(
            payment_id=payment.id,
            reason=f"reason {i}",
            refund_status=RefundStatus.PENDING,
            created_at=created_at,
        )
        refunds_repo.create(refund)

    for i in range(5):
        created_at = base_now + timedelta(seconds=i)
        refund = make_refund(
            payment_id=payment.id,
            reason=f"reason {i}",
            refund_status=RefundStatus.COMPLETED,
            created_at=created_at,
        )
        refunds_repo.create(refund)

    filters = RefundFilters(
        payment_id=payment.id,
        refund_status=RefundStatus.PENDING,
    )

    founds = refunds_repo.find_many(filters=filters)

    assert [r.reason for r in founds] == [
        "reason 4",
        "reason 3",
        "reason 2",
        "reason 1",
        "reason 0",
    ]


def test_count(make_payment, make_refund, payments_repo, refunds_repo):

    payment = make_payment()
    payments_repo.create(payment)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        created_at = base_now + timedelta(seconds=i)
        refund = make_refund(
            payment_id=payment.id,
            reason=f"reason {i}",
            refund_status=RefundStatus.PENDING,
            created_at=created_at,
        )
        refunds_repo.create(refund)

    for i in range(5):
        created_at = base_now + timedelta(seconds=i)
        refund = make_refund(
            payment_id=payment.id,
            reason=f"reason {i}",
            refund_status=RefundStatus.COMPLETED,
            created_at=created_at,
        )
        refunds_repo.create(refund)

    filters = RefundFilters(
        payment_id=payment.id,
        refund_status=RefundStatus.PENDING,
    )

    total = refunds_repo.count(filters=filters)

    assert total == 5


def test_sum(make_payment, make_refund, payments_repo, refunds_repo):

    payment = make_payment()
    payments_repo.create(payment)

    for i in range(5):
        amount = 1 + Decimal(f"{i}")
        refund = make_refund(
            payment_id=payment.id,
            amount=amount,
            refund_status=RefundStatus.PENDING,
        )
        refunds_repo.create(refund)

    for i in range(5):
        amount = 1 + Decimal(f"{i}")
        refund = make_refund(
            payment_id=payment.id,
            amount=amount,
            refund_status=RefundStatus.COMPLETED,
        )
        refunds_repo.create(refund)

    filters = RefundFilters(
        payment_id=payment.id,
        refund_status=RefundStatus.PENDING,
    )

    total_sum = refunds_repo.sum_amount(filters=filters)

    assert total_sum == Decimal("15")


def test_filter_by_payment(make_payment, make_refund, payments_repo, refunds_repo):

    payment_1 = make_payment()
    payments_repo.create(payment_1)

    payment_2 = make_payment()
    payments_repo.create(payment_2)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(3):
        created_at = base_now + timedelta(seconds=i)
        refund = make_refund(
            payment_id=payment_1.id,
            reason=f"reason {i}",
            refund_status=RefundStatus.PENDING,
            created_at=created_at,
        )
        refunds_repo.create(refund)

    for i in range(5):
        created_at = base_now + timedelta(seconds=i)
        refund = make_refund(
            payment_id=payment_2.id,
            reason=f"reason {i}",
            refund_status=RefundStatus.PENDING,
            created_at=created_at,
        )
        refunds_repo.create(refund)

    filters = RefundFilters().by_payment(payment_id=payment_1.id)

    founds = refunds_repo.find_many(filters=filters)

    assert len(founds) == 3
    assert refunds_repo.count(filters=filters) == 3

    assert all(refund.payment_id == payment_1.id for refund in founds)


def test_filter_by_appointment(
    make_payment,
    make_refund,
    make_quoted_appointment,
    payments_repo,
    refunds_repo,
    appointments_repo,
):
    payment = make_payment()
    payments_repo.create(payment)

    appointment_1 = make_quoted_appointment()
    appointment_2 = make_quoted_appointment()
    appointments_repo.create(appointment_1)
    appointments_repo.create(appointment_2)

    for i in range(3):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                appointment_id=appointment_1.id,
                reason=f"appointment_1_{i}",
            )
        )

    for i in range(5):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                appointment_id=appointment_2.id,
                reason=f"appointment_2_{i}",
            )
        )

    filters = RefundFilters.by_appointment(appointment_1.id)

    founds = refunds_repo.find_many(filters=filters)

    assert len(founds) == 3
    assert refunds_repo.count(filters=filters) == 3

    assert all(refund.appointment_id == appointment_1.id for refund in founds)


def test_filter_by_creator(
    make_payment, make_refund, make_user, payments_repo, refunds_repo, users_repo
):
    payment = make_payment()
    payments_repo.create(payment)

    creator_1 = make_user()
    creator_2 = make_user()
    users_repo.create(creator_1)
    users_repo.create(creator_2)

    for i in range(2):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                created_by_user_id=creator_1.id,
                reason=f"creator_1_{i}",
            )
        )

    for i in range(4):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                created_by_user_id=creator_2.id,
                reason=f"creator_2_{i}",
            )
        )

    filters = RefundFilters.by_creator(creator_1.id)

    founds = refunds_repo.find_many(filters=filters)

    assert len(founds) == 2
    assert refunds_repo.count(filters=filters) == 2

    assert all(refund.created_by_user_id == creator_1.id for refund in founds)


def test_filter_by_refund_method(
    make_payment,
    make_refund,
    payments_repo,
    refunds_repo,
):
    payment = make_payment()
    payments_repo.create(payment)

    for i in range(3):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                refund_method=RefundMethodType.PIX,
            )
        )

    for i in range(5):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                refund_method=RefundMethodType.CLIENT_CREDIT,
            )
        )

    filters = RefundFilters.by_refund_method(RefundMethodType.PIX)

    founds = refunds_repo.find_many(filters=filters)

    assert len(founds) == 3
    assert refunds_repo.count(filters=filters) == 3

    assert all(refund.refund_method == RefundMethodType.PIX for refund in founds)


def test_zero_filter(
    make_payment, make_refund, make_user, payments_repo, refunds_repo, users_repo
):
    payment = make_payment()
    payments_repo.create(payment)

    creator_1 = make_user()
    creator_2 = make_user()
    users_repo.create(creator_1)
    users_repo.create(creator_2)

    for i in range(2):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                created_by_user_id=creator_1.id,
                reason=f"creator_1_{i}",
            )
        )

    for i in range(4):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                created_by_user_id=creator_2.id,
                reason=f"creator_2_{i}",
            )
        )

    filters = RefundFilters()

    founds = refunds_repo.find_many(filters=filters)

    assert len(founds) == 6  # without filters find all entries


def test_find_many_order_asc(
    make_payment,
    make_refund,
    payments_repo,
    refunds_repo,
):
    payment = make_payment()
    payments_repo.create(payment)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                reason=f"reason {i}",
                created_at=base_now + timedelta(seconds=i),
            )
        )

    founds = refunds_repo.find_many(
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
    payments_repo,
    refunds_repo,
):
    payment = make_payment()
    payments_repo.create(payment)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                reason=f"reason {i}",
                created_at=base_now + timedelta(seconds=i),
            )
        )

    founds = refunds_repo.find_many(
        filters=RefundFilters(),
        limit=2,
        offset=1,
        direction=Direction.desc,
    )

    assert [r.reason for r in founds] == [
        "reason 3",
        "reason 2",
    ]


def test_filter_by_date_range(
    make_payment,
    make_refund,
    payments_repo,
    refunds_repo,
):
    payment = make_payment()
    payments_repo.create(payment)

    base_now = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        refunds_repo.create(
            make_refund(
                payment_id=payment.id,
                reason=f"reason {i}",
                created_at=base_now + timedelta(minutes=i),
            )
        )

    filters = RefundFilters(
        created_at_from=base_now + timedelta(minutes=1),
        created_at_to=base_now + timedelta(minutes=3),
    )

    founds = refunds_repo.find_many(filters=filters)

    assert len(founds) == 3

    assert {refund.reason for refund in founds} == {
        "reason 1",
        "reason 2",
        "reason 3",
    }
