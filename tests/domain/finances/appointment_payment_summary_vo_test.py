from decimal import Decimal

import pytest

from app.domain.studio.finances.entities.value_objects.appointment_payment_summary import (
    AppointmentPaymentSummary,
)


@pytest.mark.parametrize(
    ("total_paid", "total_completed_refunds", "total_pending_refunds", "expected_net_paid"),
    [
        (Decimal("100"), Decimal("0"), Decimal("0"), Decimal("100")),
        (Decimal("100"), Decimal("20"), Decimal("0"), Decimal("80")),
        (Decimal("100"), Decimal("0"), Decimal("20"), Decimal("80")),
        (Decimal("100"), Decimal("20"), Decimal("30"), Decimal("50")),
        (Decimal("100"), Decimal("100"), Decimal("0"), Decimal("0")),
        (Decimal("100"), Decimal("100"), Decimal("20"), Decimal("-20")),
    ],
)
def test_net_paid(
    total_paid,
    total_completed_refunds,
    total_pending_refunds,
    expected_net_paid,
):
    summary = AppointmentPaymentSummary(
        total_paid=total_paid,
        total_completed_refunds=total_completed_refunds,
        total_pending_refunds=total_pending_refunds,
    )

    assert summary.net_paid == expected_net_paid


@pytest.mark.parametrize(
    ("total_pending_refunds", "expected"),
    [
        (Decimal("0"), False),
        (Decimal("1"), True),
        (Decimal("100"), True),
    ],
)
def test_has_pending_refunds(total_pending_refunds, expected):
    summary = AppointmentPaymentSummary(
        total_paid=Decimal("100"),
        total_completed_refunds=Decimal("0"),
        total_pending_refunds=total_pending_refunds,
    )

    assert summary.has_pending_refunds is expected


def test_net_paid_does_not_depend_on_has_pending_refunds():
    summary = AppointmentPaymentSummary(
        total_paid=Decimal("100"),
        total_completed_refunds=Decimal("20"),
        total_pending_refunds=Decimal("30"),
    )

    assert summary.net_paid == Decimal("50")
    assert summary.has_pending_refunds is True
