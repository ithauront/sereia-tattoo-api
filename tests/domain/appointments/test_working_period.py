from datetime import time

import pytest

from app.core.exceptions.calendar import (
    AppointmentCannotLastOvernightError,
    InvalidWeekdayError,
    WorkingPeriodMustHaveRealisticTimeAndDateError,
)
from app.domain.studio.appointments.entities.working_period import WorkingPeriod


def test_invalid_weekday_over_6():
    with pytest.raises(InvalidWeekdayError):
        WorkingPeriod.create(weekday=7, start_at=time(12, 00), end_at=time(13, 00))


def test_invalid_weekday_less_than_0():
    with pytest.raises(InvalidWeekdayError):
        WorkingPeriod.create(weekday=-1, start_at=time(12, 00), end_at=time(13, 00))


def test_end_before_start():
    with pytest.raises(WorkingPeriodMustHaveRealisticTimeAndDateError):
        WorkingPeriod.create(weekday=3, start_at=time(12, 00), end_at=time(10, 00))


def test_end_equals_start():
    with pytest.raises(WorkingPeriodMustHaveRealisticTimeAndDateError):
        WorkingPeriod.create(weekday=3, start_at=time(12, 00), end_at=time(12, 00))


def test_update_with_unrealistic_time_frame():
    working_period = WorkingPeriod.create(weekday=3, start_at=time(12, 00), end_at=time(14, 00))

    with pytest.raises(WorkingPeriodMustHaveRealisticTimeAndDateError):
        working_period.update_period(start_at=time(12, 00), end_at=time(12, 00))


def test_is_available_for_true(make_datetime):
    working_period = WorkingPeriod.create(
        weekday=3,
        start_at=time(12, 0),
        end_at=time(20, 0),
    )

    available = working_period.is_available_for(
        start=make_datetime(3, 18),
        end=make_datetime(3, 20),
    )

    assert available is True


def test_is_available_for_false(make_datetime):
    working_period = WorkingPeriod.create(
        weekday=3,
        start_at=time(12, 0),
        end_at=time(14, 0),
    )

    available = working_period.is_available_for(
        start=make_datetime(3, 13),
        end=make_datetime(3, 14, 30),
    )

    assert available is False


def test_is_available_for_returns_false_when_weekday_is_different(make_datetime):
    working_period = WorkingPeriod.create(
        weekday=3,
        start_at=time(12, 0),
        end_at=time(20, 0),
    )

    available = working_period.is_available_for(
        start=make_datetime(2, 13),
        end=make_datetime(2, 14),
    )

    assert available is False


def test_is_available_for_raises_when_appointment_lasts_overnight(make_datetime):
    working_period = WorkingPeriod.create(
        weekday=3,
        start_at=time(12, 0),
        end_at=time(23, 59),
    )

    with pytest.raises(AppointmentCannotLastOvernightError):
        working_period.is_available_for(
            start=make_datetime(3, 23, 30),
            end=make_datetime(4, 0, 30),
        )
