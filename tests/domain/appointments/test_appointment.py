from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.exceptions.appointments import (
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentMustHaveRealisticTimeAndDateError,
    AppointmentProjectStateError,
    CurrentSessionMustBeLessThanTotalError,
    CurrentSessionMustBePositiveError,
    ForMultipleSessionsProjectIdMustBeDefinedError,
    TotalSessionsMustBeAtLeastTwoError,
    TotalSessionsNumberMustBeDefineError,
    TotalSessionsNumberMustBePositiveError,
)
from app.core.exceptions.validation import ValidationError
from app.core.types.appointment_enums import AppointmentStatus


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


@pytest.mark.parametrize(
    ("values", "expected_error"),
    [
        ({"total_sessions": 0}, TotalSessionsNumberMustBePositiveError),
        ({"total_sessions": -1}, TotalSessionsNumberMustBePositiveError),
        ({"total_sessions": 1}, TotalSessionsMustBeAtLeastTwoError),
        ({"current_session": 1}, TotalSessionsNumberMustBeDefineError),
        (
            {"current_session": 0, "total_sessions": 3},
            CurrentSessionMustBePositiveError,
        ),
        (
            {"current_session": -1, "total_sessions": 3},
            CurrentSessionMustBePositiveError,
        ),
        (
            {"current_session": 4, "total_sessions": 3},
            CurrentSessionMustBeLessThanTotalError,
        ),
        (
            {"current_session": 1, "total_sessions": 3},
            ForMultipleSessionsProjectIdMustBeDefinedError,
        ),
    ],
)
def test_invalid_session_state_is_rejected(make_appointment_base, values, expected_error):
    with pytest.raises(expected_error):
        make_appointment_base(**values)


def test_project_requires_multiple_session_data(make_appointment_base):
    with pytest.raises(AppointmentProjectStateError):
        make_appointment_base(project_id=uuid4())


def test_cannot_reduce_total_below_current_session(make_appointment_base):
    appointment = make_appointment_base(
        project_id=uuid4(), current_session=3, total_sessions=4
    )

    with pytest.raises(CurrentSessionMustBeLessThanTotalError):
        appointment.update_total_sessions(2)


def test_reschedule_changes_only_interval_and_preserves_project_data(make_appointment_base):
    project_id = uuid4()
    appointment = make_appointment_base(
        project_id=project_id,
        current_session=2,
        total_sessions=4,
    )
    new_start_at = datetime.now(timezone.utc) + timedelta(days=2)
    new_end_at = new_start_at + timedelta(hours=3)

    appointment.reschedule(new_start_at=new_start_at, new_end_at=new_end_at)

    assert appointment.start_at == new_start_at
    assert appointment.end_at == new_end_at
    assert appointment.project_id == project_id
    assert appointment.current_session == 2
    assert appointment.total_sessions == 4
    assert appointment.observations is not None
    assert "Horários atuais são provenientes de um reagendamento" in appointment.observations


@pytest.mark.parametrize("end_delta", [timedelta(0), timedelta(hours=-1)])
def test_reschedule_rejects_invalid_interval_without_mutating_appointment(
    end_delta, make_appointment_base
):
    appointment = make_appointment_base()
    old_start_at = appointment.start_at
    old_end_at = appointment.end_at
    new_start_at = datetime.now(timezone.utc) + timedelta(days=2)

    with pytest.raises(AppointmentMustHaveRealisticTimeAndDateError):
        appointment.reschedule(
            new_start_at=new_start_at,
            new_end_at=new_start_at + end_delta,
        )

    assert appointment.start_at == old_start_at
    assert appointment.end_at == old_end_at


def test_reschedule_rejects_past_interval_without_mutating_appointment(make_appointment_base):
    appointment = make_appointment_base()
    old_start_at = appointment.start_at
    old_end_at = appointment.end_at
    new_start_at = datetime.now(timezone.utc) - timedelta(days=2)

    with pytest.raises(AppointmentMustHaveRealisticTimeAndDateError):
        appointment.reschedule(
            new_start_at=new_start_at,
            new_end_at=new_start_at + timedelta(hours=2),
        )

    assert appointment.start_at == old_start_at
    assert appointment.end_at == old_end_at


def test_reschedule_rejects_naive_datetimes_without_mutating_appointment(make_appointment_base):
    appointment = make_appointment_base()
    old_start_at = appointment.start_at
    old_end_at = appointment.end_at
    new_start_at = datetime.now() + timedelta(days=2)

    with pytest.raises(AppointmentMustHaveRealisticTimeAndDateError):
        appointment.reschedule(
            new_start_at=new_start_at,
            new_end_at=new_start_at + timedelta(hours=2),
        )

    assert appointment.start_at == old_start_at
    assert appointment.end_at == old_end_at


@pytest.mark.parametrize(
    "status",
    [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELED],
)
def test_reschedule_rejects_terminal_status_without_mutating_appointment(
    status, make_appointment_base
):
    appointment = make_appointment_base(status=status)
    old_start_at = appointment.start_at
    old_end_at = appointment.end_at
    new_start_at = datetime.now(timezone.utc) + timedelta(days=2)

    with pytest.raises(AppointmentMustBeInCorrectPreviousStatusError):
        appointment.reschedule(
            new_start_at=new_start_at,
            new_end_at=new_start_at + timedelta(hours=2),
        )

    assert appointment.start_at == old_start_at
    assert appointment.end_at == old_end_at
