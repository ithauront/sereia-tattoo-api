from datetime import datetime, time, timezone
from uuid import UUID, uuid4

from app.core.exceptions.calendar import (
    AppointmentCannotLastOvernightError,
    InvalidWeekdayError,
    WorkingPeriodMustHaveRealisticTimeAndDateError,
)


class WorkingPeriod:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        weekday: int,
        start_at: time,
        end_at: time,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        now = self._utc_now()

        if weekday < 0 or weekday > 6:
            raise InvalidWeekdayError()

        self.id = id or uuid4()
        self.weekday = weekday
        self.start_at = start_at
        self.end_at = end_at
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @classmethod
    def create(
        cls,
        *,
        weekday: int,
        start_at: time,
        end_at: time,
    ) -> "WorkingPeriod":
        if end_at <= start_at:
            raise WorkingPeriodMustHaveRealisticTimeAndDateError()
        if weekday < 0 or weekday > 6:
            raise InvalidWeekdayError()

        return cls(weekday=weekday, start_at=start_at, end_at=end_at)

    def update_period(self, *, start_at: time, end_at: time):
        if end_at <= start_at:
            raise WorkingPeriodMustHaveRealisticTimeAndDateError()
        self.start_at = start_at
        self.end_at = end_at
        self._touch()

    def is_available_for(self, *, start: datetime, end: datetime) -> bool:
        """
        Check if a time range fits inside this working period.
        Return if user is available for the time range
        """
        weekday_start = start.weekday()
        weekday_end = end.weekday()

        if weekday_start != weekday_end:
            raise AppointmentCannotLastOvernightError()

        if self.weekday != weekday_start:
            return False

        return self.start_at <= start.time() and end.time() <= self.end_at

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def _touch(self):
        self.updated_at = datetime.now(timezone.utc)
