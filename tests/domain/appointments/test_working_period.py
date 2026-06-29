from datetime import time

import pytest

from app.core.exceptions.calendar import (
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


def test_is_avaiable_for_true():
    working_period = WorkingPeriod.create(weekday=3, start_at=time(12, 00), end_at=time(20, 00))

    available = working_period.is_available_for(start=time(18, 00), end=time(20, 00))

    assert available is True


def test_is_avaiable_for_false():
    working_period = WorkingPeriod.create(weekday=3, start_at=time(12, 00), end_at=time(14, 00))

    available = working_period.is_available_for(start=time(13, 00), end=time(14, 30))

    assert available is False
