import pytest
from app.core.exceptions.validation import ValidationError
from app.core.validations.username import validate_username


def test_username_validaton_success():
    username = "Jhon_doe-1."
    validate = validate_username(username)

    assert validate is None


def test_username_not_sent():
    username = ""
    with pytest.raises(ValidationError, match="username_required"):
        validate_username(username)


def test_username_with_spaces():
    username = "Jhon doe 1."
    with pytest.raises(ValidationError, match="username_cannot_contain_spaces"):
        validate_username(username)


def test_username_too_short():
    username = "Jh"
    with pytest.raises(
        ValidationError, match="username_must_have_between_3_and_30_characters"
    ):
        validate_username(username)


def test_username_too_long():
    username = "Jhon_doe-1.aBcDeF1_2_3_4_5_6_7_8"  # more than 30 char
    with pytest.raises(
        ValidationError, match="username_must_have_between_3_and_30_characters"
    ):
        validate_username(username)


def test_username_without_letters():
    username = "123"
    with pytest.raises(ValidationError, match="username_must_contain_letters"):
        validate_username(username)


def test_username_invalid_character():
    username = "Jhon_doe-1!"
    with pytest.raises(ValidationError, match="username_invalid_characters"):
        validate_username(username)
