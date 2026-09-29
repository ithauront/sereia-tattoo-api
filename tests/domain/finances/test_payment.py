from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.core.exceptions.payment import (
    InvalidPaymentAllocationStateError,
    InvalidPaymentAmountError,
    PaymentAllocationChangeMustHaveAwareDatetimeError,
    PaymentAmountExceedsMaximumError,
    PaymentAmountHasSubCentPrecisionError,
    PaymentMustBeGreaterThanZeroError,
    PaymentMustHaveDepositPurposeError,
)
from app.core.exceptions.validation import ValidationError
from app.core.types.payment_enums import (
    PaymentAllocationStatus,
    PaymentMethodType,
    PaymentPurposeType,
)


def test_method_not_enum_raises_error(make_payment):
    with pytest.raises(ValidationError) as exc:
        make_payment(payment_method="unknown_method")

    assert "Invalid value" in str(exc.value)


def test_method_not_enum_correct_string_success(make_payment):
    payment = make_payment(payment_method="cash")

    assert payment.payment_method == PaymentMethodType.CASH


def test_method_enum_success(make_payment):
    payment = make_payment(payment_method=PaymentMethodType.CASH)

    assert payment.payment_method == PaymentMethodType.CASH


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (Decimal("10"), Decimal("10.00")),
        (Decimal("10.5"), Decimal("10.50")),
        (Decimal("10.50"), Decimal("10.50")),
        (Decimal("10.500"), Decimal("10.50")),
    ],
)
def test_valid_amount_is_normalized_to_two_decimal_places(make_payment, amount, expected):
    payment = make_payment(amount=amount)

    assert payment.amount == expected
    assert payment.amount.as_tuple().exponent == -2


@pytest.mark.parametrize("amount", [Decimal("10.001"), Decimal("10.999")])
def test_amount_with_sub_cent_precision_raises_error(make_payment, amount):
    with pytest.raises(PaymentAmountHasSubCentPrecisionError):
        make_payment(amount=amount)


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-0.01")])
def test_non_positive_amount_raises_error(make_payment, amount):
    with pytest.raises(PaymentMustBeGreaterThanZeroError):
        make_payment(amount=amount)


@pytest.mark.parametrize("amount", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_non_finite_amount_raises_error(make_payment, amount):
    with pytest.raises(InvalidPaymentAmountError):
        make_payment(amount=amount)


def test_maximum_amount_is_accepted(make_payment):
    payment = make_payment(amount=Decimal("99999999.99"))

    assert payment.amount == Decimal("99999999.99")


def test_amount_above_database_precision_raises_error(make_payment):
    with pytest.raises(PaymentAmountExceedsMaximumError):
        make_payment(amount=Decimal("100000000.00"))


def test_new_payment_has_active_allocation(make_payment):
    payment = make_payment()

    assert payment.allocation_status == PaymentAllocationStatus.ACTIVE
    assert payment.allocation_changed_at is None
    assert payment.allocation_change_reason is None


def test_retain_deposit_preserves_original_purpose(make_payment):
    retained_at = datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc)
    payment = make_payment(payment_purpose=PaymentPurposeType.DEPOSIT)

    payment.retain_deposit(reason="  Reagendamento fora do prazo  ", retained_at=retained_at)

    assert payment.payment_purpose == PaymentPurposeType.DEPOSIT
    assert payment.allocation_status == PaymentAllocationStatus.RETAINED
    assert payment.allocation_changed_at == retained_at
    assert payment.allocation_change_reason == "Reagendamento fora do prazo"


def test_retain_deposit_is_idempotent_and_preserves_first_change(make_payment):
    first_retained_at = datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc)
    payment = make_payment(payment_purpose=PaymentPurposeType.DEPOSIT)
    payment.retain_deposit(reason="Primeiro motivo de retenção", retained_at=first_retained_at)

    payment.retain_deposit(
        reason="Um motivo posterior não deve sobrescrever o original",
        retained_at=datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc),
    )

    assert payment.allocation_changed_at == first_retained_at
    assert payment.allocation_change_reason == "Primeiro motivo de retenção"


def test_cannot_retain_payment_that_is_not_a_deposit(make_payment):
    payment = make_payment(payment_purpose=PaymentPurposeType.APPOINTMENT)

    with pytest.raises(PaymentMustHaveDepositPurposeError):
        payment.retain_deposit(
            reason="Reagendamento fora do prazo",
            retained_at=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
        )


def test_retain_deposit_requires_timezone_aware_datetime(make_payment):
    payment = make_payment(payment_purpose=PaymentPurposeType.DEPOSIT)

    with pytest.raises(PaymentAllocationChangeMustHaveAwareDatetimeError):
        payment.retain_deposit(
            reason="Reagendamento fora do prazo",
            retained_at=datetime(2026, 1, 2, 10, 0),
        )


def test_non_deposit_cannot_be_hydrated_as_retained(make_payment):
    with pytest.raises(InvalidPaymentAllocationStateError):
        make_payment(
            payment_purpose=PaymentPurposeType.APPOINTMENT,
            allocation_status=PaymentAllocationStatus.RETAINED,
            allocation_changed_at=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
            allocation_change_reason="Reagendamento fora do prazo",
        )
