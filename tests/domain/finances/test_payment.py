from decimal import Decimal

import pytest

from app.core.exceptions.payment import (
    InvalidPaymentAmountError,
    PaymentAmountExceedsMaximumError,
    PaymentAmountHasSubCentPrecisionError,
    PaymentMustBeGreaterThanZeroError,
)
from app.core.exceptions.validation import ValidationError
from app.core.types.payment_enums import PaymentMethodType


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
