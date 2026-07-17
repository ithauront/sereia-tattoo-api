from datetime import datetime

from app.core.exceptions.appointments import (
    SlotIsNotAvailableError,
)
from app.core.exceptions.calendar import UserIsNotWorkingInDesignatedTimeframeError
from app.core.types.calendar_enums import CalendarExceptionType
from app.domain.studio.appointments.entities.calendar_exception import CalendarException
from app.domain.studio.appointments.entities.calendar_settings import CalendarSettings


# TODO: fazer testes
class CalendarAvailabilityPolicy:
    def can_schedule(
        self,
        *,
        calendar_settings: CalendarSettings,
        calendar_exceptions: list[CalendarException],
        start_at: datetime,
        end_at: datetime,
        can_ignore_booking_window: bool,
    ) -> None:

        effective_exception = self._find_effective_exception(calendar_exceptions)

        if effective_exception is not None:
            if effective_exception.exception_type == CalendarExceptionType.BLOCK:
                raise UserIsNotWorkingInDesignatedTimeframeError()
            return

        inside_booking_window = calendar_settings.is_inside_booking_window(start=start_at)
        if not inside_booking_window and not can_ignore_booking_window:
            raise SlotIsNotAvailableError()

        inside_working_period = calendar_settings.is_inside_working_period(start=start_at, end=end_at)

        if not inside_working_period:
            raise UserIsNotWorkingInDesignatedTimeframeError()

    def _find_effective_exception(
        self,
        exceptions: list[CalendarException],
    ) -> CalendarException | None:

        if not exceptions:
            return None

        return min(
            exceptions,
            key=lambda exception: (
                exception.end_at - exception.start_at,
                exception.exception_type != CalendarExceptionType.BLOCK,
            ),
        )
