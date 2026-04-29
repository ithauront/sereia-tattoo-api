import pytest

from app.core.exceptions.validation import ValidationError
from app.domain.studio.appointments.enums.appointment_enums import AppointmentStatus


def test_unknown_status_raises_error(make_appointment_base):
    with pytest.raises(ValidationError) as exc:
        make_appointment_base(status="unknown_status")

    assert "Invalid value" in str(exc.value)


def test_corretct_status_not_enum_success(make_appointment_base):
    appointment = make_appointment_base(status="requested")

    assert appointment.status == AppointmentStatus.REQUESTED


def test_status_enum_success(make_appointment_base):
    appointment = make_appointment_base(status=AppointmentStatus.REQUESTED)

    assert appointment.status == AppointmentStatus.REQUESTED


def test_status_none_error(make_appointment_base):
    with pytest.raises(ValidationError) as exc:
        make_appointment_base(status=None)
    assert "Invalid value" in str(exc.value)


def test_type_must_be_enum(make_appointment_base):
    with pytest.raises(ValidationError) as exc:
        make_appointment_base(appointment_type="unknown_type")
    assert "Invalid value" in str(exc.value)
