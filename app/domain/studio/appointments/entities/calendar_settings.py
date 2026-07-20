from datetime import date, datetime, time, timezone
from typing import List
from uuid import UUID

from app.core.exceptions.calendar import (
    BookingWindowMustBeInTheFutureError,
    WorkingPeriodsNotFoundError,
    WorkingPeriodsOverlapError,
)
from app.domain.studio.appointments.entities.working_period import WorkingPeriod
from app.domain.studio.appointments.events.booking_window_updated import BookingWindowUpdated


class CalendarSettings:
    def __init__(
        self,
        *,
        user_id: UUID,
        booking_window_until: date,
        working_periods: List[WorkingPeriod],
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):

        now = self._utc_now()

        self.user_id = user_id
        self.booking_window_until = booking_window_until
        self.working_periods = working_periods
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @classmethod
    def create(
        cls,
        *,
        user_id: UUID,
        booking_window_until: date,
        working_periods: List[WorkingPeriod],
    ) -> "CalendarSettings":
        if cls._utc_now().date() > booking_window_until:
            raise BookingWindowMustBeInTheFutureError()

        cls.validate_working_periods(working_periods)

        return cls(
            user_id=user_id,
            booking_window_until=booking_window_until,
            working_periods=working_periods,
        )

    def update_booking_window(self, booking_window_until: date) -> BookingWindowUpdated:
        if self._utc_now().date() > booking_window_until:
            raise BookingWindowMustBeInTheFutureError()

        self.booking_window_until = booking_window_until
        self._touch()

        return BookingWindowUpdated(user_id=self.user_id, new_booking_window=booking_window_until)

    def add_working_period(self, period: WorkingPeriod):

        self.validate_working_periods(self.working_periods + [period])

        self.working_periods.append(period)
        self._touch()

    def update_working_period(
        self,
        *,
        period_id: UUID,
        start_at: time,
        end_at: time,
    ):
        period = next((period for period in self.working_periods if period.id == period_id), None)

        if period is None:
            raise WorkingPeriodsNotFoundError()

        updated = WorkingPeriod(
            id=period.id,
            weekday=period.weekday,
            start_at=start_at,
            end_at=end_at,
        )

        others = [period for period in self.working_periods if period.id != period_id]

        self.validate_working_periods(others + [updated])

        period.update_period(start_at=start_at, end_at=end_at)

        self._touch()

    def replace_working_periods(self, working_periods: List[WorkingPeriod]):
        # This method replace the whole working periods group
        self.validate_working_periods(working_periods)
        self.working_periods = working_periods
        self._touch()

    def remove_working_period(self, period_id: UUID):
        self.working_periods = [period for period in self.working_periods if period.id != period_id]

        self._touch()

    def is_inside_working_period(self, *, start: datetime, end: datetime) -> bool:

        return any(
            working_period.is_available_for(start=start, end=end)
            for working_period in self.working_periods
        )

    def is_inside_booking_window(self, *, start: datetime) -> bool:
        return start >= self._utc_now() and start.date() <= self.booking_window_until

    @staticmethod
    def validate_working_periods(
        working_periods: List[WorkingPeriod],
    ):
        sorted_periods = sorted(working_periods, key=lambda period: (period.weekday, period.start_at))

        for current, next_period in zip(
            sorted_periods,
            sorted_periods[1:],
        ):
            if current.weekday == next_period.weekday and current.end_at > next_period.start_at:
                raise WorkingPeriodsOverlapError()

    def _touch(self):
        self.updated_at = self._utc_now()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)
