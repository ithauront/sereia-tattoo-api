from datetime import datetime, time, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.exceptions.calendar import (
    BookingWindowMustBeInTheFutureError,
    WorkingPeriodsNotFoundError,
    WorkingPeriodsOverlapError,
)
from app.domain.studio.appointments.entities.calendar_settings import CalendarSettings


def test_booking_window_on_past(make_working_period, make_user):
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=30)
    booking_in_past_date = past.date()

    user = make_user()

    working_period = [make_working_period()]

    with pytest.raises(BookingWindowMustBeInTheFutureError):
        CalendarSettings.create(
            user_id=user.id, booking_window_until=booking_in_past_date, working_periods=working_period
        )


def test_working_periods_overlap(make_working_period, make_user):
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)
    booking_in_future_date = future.date()

    user = make_user()

    working_period = [
        make_working_period(start_at=time(8, 00), end_at=time(12, 00), weekday=1),
        make_working_period(start_at=time(11, 00), end_at=time(18, 00), weekday=1),
    ]

    with pytest.raises(WorkingPeriodsOverlapError):
        CalendarSettings.create(
            user_id=user.id, booking_window_until=booking_in_future_date, working_periods=working_period
        )


def test_update_to_past_window(make_working_period, make_user):
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)
    booking_in_future_date = future.date()

    past = now - timedelta(days=30)
    booking_in_past_date = past.date()

    user = make_user()

    working_period = [
        make_working_period(start_at=time(8, 00), end_at=time(12, 00), weekday=1),
    ]

    calendar = CalendarSettings.create(
        user_id=user.id, booking_window_until=booking_in_future_date, working_periods=working_period
    )
    with pytest.raises(BookingWindowMustBeInTheFutureError):
        calendar.update_booking_window(booking_window_until=booking_in_past_date)


def test_update_inexistent_working_period(make_working_period, make_user):
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)
    booking_in_future_date = future.date()

    user = make_user()

    working_period = [
        make_working_period(start_at=time(8, 00), end_at=time(12, 00), weekday=1),
    ]

    calendar = CalendarSettings.create(
        user_id=user.id, booking_window_until=booking_in_future_date, working_periods=working_period
    )

    with pytest.raises(WorkingPeriodsNotFoundError):
        calendar.update_working_period(period_id=uuid4(), start_at=time(18, 00), end_at=time(22, 00))


def test_is_inside_working_period_true(make_working_period, make_user, make_datetime):
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)

    user = make_user()

    working_periods = [
        make_working_period(
            weekday=1,
            start_at=time(8, 0),
            end_at=time(12, 0),
        )
    ]

    calendar = CalendarSettings.create(
        user_id=user.id,
        booking_window_until=future.date(),
        working_periods=working_periods,
    )

    is_inside = calendar.is_inside_working_period(
        start=make_datetime(1, 9),
        end=make_datetime(1, 10),
    )

    assert is_inside is True


def test_is_inside_working_period_false(make_working_period, make_user, make_datetime):
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)

    user = make_user()

    working_periods = [
        make_working_period(
            weekday=1,
            start_at=time(8, 0),
            end_at=time(12, 0),
        )
    ]

    calendar = CalendarSettings.create(
        user_id=user.id,
        booking_window_until=future.date(),
        working_periods=working_periods,
    )

    is_inside = calendar.is_inside_working_period(
        start=make_datetime(1, 11),
        end=make_datetime(1, 13),
    )

    assert is_inside is False
