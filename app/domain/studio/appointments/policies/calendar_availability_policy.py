from datetime import datetime

from app.core.exceptions.appointments import (
    SlotIsNotAvailableError,
)
from app.core.exceptions.calendar import UserIsNotWorkingInDesignatedTimeframeError
from app.core.types.calendar_enums import CalendarExceptionType
from app.domain.studio.appointments.entities.calendar_exception import CalendarException
from app.domain.studio.appointments.entities.calendar_settings import CalendarSettings


class CalendarAvailabilityPolicy:
    def can_reschedule(
        self,
        *,
        calendar_settings: CalendarSettings,
        calendar_exceptions: list[CalendarException],
        new_start_at: datetime,
        new_end_at: datetime,
        can_ignore_booking_window: bool,
    ) -> None:

        self.can_schedule(
            calendar_settings=calendar_settings,
            calendar_exceptions=calendar_exceptions,
            start_at=new_start_at,
            end_at=new_end_at,
            can_ignore_booking_window=can_ignore_booking_window,
        )

    def can_schedule(
        self,
        *,
        calendar_settings: CalendarSettings,
        calendar_exceptions: list[CalendarException],
        start_at: datetime,
        end_at: datetime,
        can_ignore_booking_window: bool,
    ) -> None:

        intervals = self._split_interval(
            start_at=start_at, end_at=end_at, exceptions=calendar_exceptions
        )

        for interval_start, interval_end in intervals:
            applicable_exceptions = [
                exception
                for exception in calendar_exceptions
                if exception.start_at <= interval_start and exception.end_at >= interval_end
            ]
            effective_exception = self._find_effective_exception(applicable_exceptions)

            if effective_exception is not None:
                if effective_exception.exception_type == CalendarExceptionType.BLOCK:
                    raise UserIsNotWorkingInDesignatedTimeframeError()
                continue

            inside_booking_window = calendar_settings.is_inside_booking_window(start=interval_start)
            if not inside_booking_window and not can_ignore_booking_window:
                raise SlotIsNotAvailableError()

            inside_working_period = calendar_settings.is_inside_working_period(
                start=interval_start, end=interval_end
            )

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

    def _split_interval(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        exceptions: list[CalendarException],
    ) -> list[tuple[datetime, datetime]]:
        boundaries = {start_at, end_at}

        for exception in exceptions:
            if start_at < exception.start_at < end_at:
                boundaries.add(exception.start_at)

            if start_at < exception.end_at < end_at:
                boundaries.add(exception.end_at)

        ordered_boundaries = sorted(boundaries)

        return list(zip(ordered_boundaries, ordered_boundaries[1:]))
