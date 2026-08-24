from datetime import datetime, timedelta, timezone

import pytest

from app.core.exceptions.appointments import SlotIsNotAvailableError
from app.core.exceptions.calendar import UserIsNotWorkingInDesignatedTimeframeError
from app.core.types.calendar_enums import CalendarExceptionType
from app.domain.studio.appointments.policies.calendar_availability_policy import (
    CalendarAvailabilityPolicy,
)


def test_inside_booking_window_and_working_period_and_no_exceptions(make_calendar_settings, make_user):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(
        days=1
    )  # If we use nextday we will not encounter error due to real now time in entity
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    policy = CalendarAvailabilityPolicy()

    result = policy.can_schedule(
        calendar_settings=calendar_settings,
        calendar_exceptions=[],
        can_ignore_booking_window=False,
        start_at=start_at,
        end_at=end_at,
    )

    assert result is None


def test_effective_exception_is_none_should_return(make_calendar_settings, make_user):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)
    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    policy = CalendarAvailabilityPolicy()

    result = policy.can_schedule(
        calendar_settings=calendar_settings,
        calendar_exceptions=[],
        can_ignore_booking_window=True,
        start_at=start_at,
        end_at=end_at,
    )

    assert result is None


def test_effective_exception_block_should_raise_error(
    make_calendar_settings, make_user, make_calendar_exception
):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    exception = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=end_at,
        exception_type=CalendarExceptionType.BLOCK,
    )

    policy = CalendarAvailabilityPolicy()

    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        policy.can_schedule(
            calendar_settings=calendar_settings,
            calendar_exceptions=[exception],
            can_ignore_booking_window=True,
            start_at=start_at,
            end_at=end_at,
        )


def test_can_ignore_booking_window_future(make_calendar_settings, make_user, make_calendar_exception):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)
    start_at_future_outside_booking_window = start_at + timedelta(days=60)
    end_at_future_outside_booking_window = end_at + timedelta(days=60)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    policy = CalendarAvailabilityPolicy()

    result = policy.can_schedule(
        calendar_settings=calendar_settings,
        calendar_exceptions=[],
        can_ignore_booking_window=True,
        start_at=start_at_future_outside_booking_window,
        end_at=end_at_future_outside_booking_window,
    )

    assert result is None


def test_can_ignore_booking_window_past(make_calendar_settings, make_user, make_calendar_exception):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)
    start_at_past_outside_booking_window = start_at - timedelta(days=60)
    end_at_past_outside_booking_window = end_at - timedelta(days=60)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    policy = CalendarAvailabilityPolicy()

    result = policy.can_schedule(
        calendar_settings=calendar_settings,
        calendar_exceptions=[],
        can_ignore_booking_window=True,
        start_at=start_at_past_outside_booking_window,
        end_at=end_at_past_outside_booking_window,
    )

    assert result is None


def test_outside_booking_window_sould_raise_error_if_cannot_ignore(
    make_calendar_settings, make_user, make_calendar_exception
):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)
    start_at_past_outside_booking_window = start_at - timedelta(days=60)
    end_at_past_outside_booking_window = end_at - timedelta(days=60)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    policy = CalendarAvailabilityPolicy()

    with pytest.raises(SlotIsNotAvailableError):
        policy.can_schedule(
            calendar_settings=calendar_settings,
            calendar_exceptions=[],
            can_ignore_booking_window=False,
            start_at=start_at_past_outside_booking_window,
            end_at=end_at_past_outside_booking_window,
        )


def test_outside_working_period(make_calendar_settings, make_user):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=22)
    end_at = next_day + timedelta(hours=23)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    policy = CalendarAvailabilityPolicy()

    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        policy.can_schedule(
            calendar_settings=calendar_settings,
            calendar_exceptions=[],
            can_ignore_booking_window=False,
            start_at=start_at,
            end_at=end_at,
        )


def test_exception_is_allow(make_calendar_settings, make_user, make_calendar_exception):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    exception = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=end_at,
        exception_type=CalendarExceptionType.ALLOW,
    )

    policy = CalendarAvailabilityPolicy()

    result = policy.can_schedule(
        calendar_settings=calendar_settings,
        calendar_exceptions=[exception],
        can_ignore_booking_window=False,
        start_at=start_at,
        end_at=end_at,
    )

    assert result is None


def test_block_smaller_than_allow(make_calendar_settings, make_user, make_calendar_exception):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    exception_allow = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=end_at + timedelta(hours=10),
        exception_type=CalendarExceptionType.ALLOW,
    )
    exception_block = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=end_at + timedelta(hours=3),
        exception_type=CalendarExceptionType.BLOCK,
    )

    policy = CalendarAvailabilityPolicy()

    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        policy.can_schedule(
            calendar_settings=calendar_settings,
            calendar_exceptions=[exception_allow, exception_block],
            can_ignore_booking_window=False,
            start_at=start_at,
            end_at=end_at,
        )


def test_block_greater_than_allow(make_calendar_settings, make_user, make_calendar_exception):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    exception_allow = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=end_at + timedelta(hours=3),
        exception_type=CalendarExceptionType.ALLOW,
    )
    exception_block = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=end_at + timedelta(hours=10),
        exception_type=CalendarExceptionType.BLOCK,
    )

    policy = CalendarAvailabilityPolicy()

    result = policy.can_schedule(
        calendar_settings=calendar_settings,
        calendar_exceptions=[exception_allow, exception_block],
        can_ignore_booking_window=False,
        start_at=start_at,
        end_at=end_at,
    )

    assert result is None


def test_block_same_size_of_allow(make_calendar_settings, make_user, make_calendar_exception):
    base_now = datetime.now(timezone.utc).replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )
    next_day = base_now + timedelta(days=1)
    booking_window_until = (base_now + timedelta(days=30)).date()
    start_at = next_day + timedelta(hours=1)
    end_at = next_day + timedelta(hours=2)

    user = make_user()

    calendar_settings = make_calendar_settings(
        user_id=user.id, booking_window_until=booking_window_until
    )

    exception_allow = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=end_at + timedelta(hours=10),
        exception_type=CalendarExceptionType.ALLOW,
    )
    exception_block = make_calendar_exception(
        calendar_of_user=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=end_at + timedelta(hours=10),
        exception_type=CalendarExceptionType.BLOCK,
    )

    policy = CalendarAvailabilityPolicy()

    with pytest.raises(UserIsNotWorkingInDesignatedTimeframeError):
        policy.can_schedule(
            calendar_settings=calendar_settings,
            calendar_exceptions=[exception_allow, exception_block],
            can_ignore_booking_window=False,
            start_at=start_at,
            end_at=end_at,
        )
