import pytest

from app.core.exceptions.validation import ValidationError


# TODO: fazer testes para enums e regras de outras entidades
def test_status_must_be_enum(make_appointment_base):
    with pytest.raises(ValidationError) as exc:
        make_appointment_base(status="unknown_status")

    assert "Invalid value" in str(exc.value)


def test_status_none_error(make_appointment_base):
    with pytest.raises(ValidationError) as exc:
        make_appointment_base(status=None)
    assert "Invalid value" in str(exc.value)


def test_type_must_be_enum(make_appointment_base):
    with pytest.raises(ValidationError) as exc:
        make_appointment_base(appointment_type="unknown_type")
    assert "Invalid value" in str(exc.value)
