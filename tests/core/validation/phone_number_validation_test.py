import pytest

from app.core.exceptions.validation import ValidationError
from app.core.validations.phone_number import validate_phone_number


def test_phone_number_validation_success():
    phone = "1123456789"  # len(10) for residency phone valid DDD (11)
    validate = validate_phone_number(phone)

    assert validate is None


def test_cell_phone_number_validation_success():
    phone = "11923456789"  # len(11) for cell phone and starts with 9 valid DDD (11)
    validate = validate_phone_number(phone)

    assert validate is None


def test_number_not_provided():
    phone = ""
    with pytest.raises(ValidationError, match="phone_required"):
        validate_phone_number(phone)


def test_invalid_phone_number():
    phone = "this_is_not_a_phone_number"
    with pytest.raises(ValidationError, match="phone_must_contain_only_numbers"):
        validate_phone_number(phone)


def test_phone_number_too_short():
    phone = "123"
    with pytest.raises(ValidationError, match="phone_must_have_10_or_11_digits"):
        validate_phone_number(phone)


def test_phone_number_too_long():
    phone = "123456789101112"
    with pytest.raises(ValidationError, match="phone_must_have_10_or_11_digits"):
        validate_phone_number(phone)


def test_phone_number_invalid_ddd():
    phone = "1023456789"  # 10 is an invalid DDD
    with pytest.raises(ValidationError, match="phone_invalid_ddd"):
        validate_phone_number(phone)


def test_cell_phone_number_invalid():
    phone = "11823456789"  # a cell phone must start with 9 after DDD
    with pytest.raises(ValidationError, match="mobile_phone_must_start_with_9"):
        validate_phone_number(phone)
