import pytest

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
