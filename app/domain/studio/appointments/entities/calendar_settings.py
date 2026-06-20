from datetime import date, datetime, time, timezone
from typing import List
from uuid import UUID

from app.core.exceptions.calendar import (
    BookingWindowMustBeInTheFutureError,
    InvalidWeekdayError,
    WorkingPeriodsOverlapError,
)
from app.domain.studio.appointments.entities.working_period import WorkingPeriod
from app.domain.studio.appointments.events.booking_window_updated import BookingWindowUpdated


# TODO: completar fazendo os metodos e tudo mais
# TODO: fazer repo
# TODO: fazer sql model and repo
# TODO: fazer fake repo e teste do repo real e fake
class CalendarSettings:
    DEFAULT_BLOCKED_WEEKDAYS = {6}  # sunday

    def __init__(
        self,
        *,
        provider_id: UUID,
        booking_window_until: date,
        blocked_weekdays: set[int] | None = None,
        working_periods: List[WorkingPeriod],
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):

        user_blocked = set(blocked_weekdays or set())

        now = self._utc_now()

        self.provider_id = provider_id
        self.booking_window_until = booking_window_until
        self.blocked_weekdays = self.DEFAULT_BLOCKED_WEEKDAYS.union(user_blocked)
        self.working_periods = working_periods
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @classmethod
    def create(
        cls,
        *,
        provider_id: UUID,
        booking_window_until: date,
        blocked_weekdays: set[int] | None = None,
        working_periods: List[WorkingPeriod],
    ) -> "CalendarSettings":
        if cls._utc_now().date() > booking_window_until:
            raise BookingWindowMustBeInTheFutureError()

        cls.validate_weekdays(blocked_weekdays)
        cls.validate_working_periods(working_periods)

        return cls(
            provider_id=provider_id,
            booking_window_until=booking_window_until,
            blocked_weekdays=blocked_weekdays,
            working_periods=working_periods,
        )

    def update_booking_window(self, booking_window_until: date) -> BookingWindowUpdated:
        if self._utc_now().date() > booking_window_until:
            raise BookingWindowMustBeInTheFutureError()

        self.booking_window_until = booking_window_until
        self._touch()

        return BookingWindowUpdated(user_id=self.provider_id, new_booking_window=booking_window_until)

    def replace_blocked_weekdays(self, blocked_weekdays: set[int]):
        self.validate_weekdays(blocked_weekdays)

        user_blocked = set(blocked_weekdays or set())
        self.blocked_weekdays = self.DEFAULT_BLOCKED_WEEKDAYS.union(user_blocked)

        self._touch()

    def replace_working_periods(self, working_periods: List[WorkingPeriod]):
        self.validate_working_periods(working_periods)

        self.working_periods = working_periods

        self._touch()

    def is_inside_working_period(self, *, start: time, end: time) -> bool:
        return any(
            working_period.is_available_for(start=start, end=end)
            for working_period in self.working_periods
        )

    def is_weekday_blocked(self, weekday: int) -> bool:
        self.validate_weekdays({weekday})

        return weekday in self.blocked_weekdays

    @staticmethod
    def validate_weekdays(blocked_weekdays: set[int] | None):
        blocked_weekdays = blocked_weekdays or set()

        invalid_days = {day for day in blocked_weekdays if day < 0 or day > 6}

        if invalid_days:
            raise InvalidWeekdayError()

    @staticmethod
    def validate_working_periods(
        working_periods: List[WorkingPeriod],
    ):
        sorted_periods = sorted(
            working_periods,
            key=lambda period: period.start_at,
        )

        for current, next_period in zip(
            sorted_periods,
            sorted_periods[1:],
        ):
            if current.end_at > next_period.start_at:
                raise WorkingPeriodsOverlapError()

    def _touch(self):
        self.updated_at = self._utc_now()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)
