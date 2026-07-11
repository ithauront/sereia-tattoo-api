from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.exceptions.calendar import (
    CalendarExceptionMustHaveRealisticTimeAndDateError,
    InvalidReasonError,
)
from app.core.types.calendar_enums import CalendarExceptionType
from app.domain.utils.ensure_enum import ensure_enum


class CalendarException:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        calendar_of_user: UUID,
        start_at: datetime,
        end_at: datetime,
        exception_type: CalendarExceptionType,
        reason: str | None = None,
        created_by: UUID,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        now = self._utc_now()

        self.id = id or uuid4()
        self.start_at = start_at
        self.end_at = end_at
        self.exception_type = ensure_enum(exception_type, CalendarExceptionType)
        self.calendar_of_user = calendar_of_user
        self.reason = reason
        self.created_by = created_by
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @classmethod
    def create(
        cls,
        *,
        calendar_of_user: UUID,
        start_at: datetime,
        end_at: datetime,
        exception_type: CalendarExceptionType,
        reason: str | None,
        created_by: UUID,
    ) -> "CalendarException":
        if end_at <= start_at:
            raise CalendarExceptionMustHaveRealisticTimeAndDateError()

        now = cls._utc_now()
        if start_at < now:
            raise CalendarExceptionMustHaveRealisticTimeAndDateError()

        return cls(
            calendar_of_user=calendar_of_user,
            start_at=start_at,
            end_at=end_at,
            exception_type=exception_type,
            reason=reason,
            created_by=created_by,
        )

    def reschedule(self, *, start_at: datetime, end_at: datetime):
        if end_at <= start_at:
            raise CalendarExceptionMustHaveRealisticTimeAndDateError()

        now = self._utc_now()
        if start_at < now:
            raise CalendarExceptionMustHaveRealisticTimeAndDateError()

        self.start_at = start_at
        self.end_at = end_at

        self._touch()

    def change_type(self, *, new_exception_type: CalendarExceptionType) -> bool:
        if self.exception_type == new_exception_type:
            return False

        self.exception_type = new_exception_type
        self._touch()
        return True

    def update_reason(self, reason: str):
        if not reason or not reason.strip():
            raise InvalidReasonError()

        self.reason = reason

        self._touch()

    def overlaps(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        return self.start_at < end_at and self.end_at > start_at

    def is_active(self) -> bool:
        now = self._utc_now()
        return self.start_at <= now <= self.end_at

    def _touch(self):
        self.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)
