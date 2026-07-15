class WorkingPeriodMustHaveRealisticTimeAndDateError(Exception):
    pass


class CannotFindWorkingPeriodsForThisUserError(Exception):
    pass


class UserIsNotWorkingInDesignatedTimeframeError(Exception):
    pass


class AppointmentCannotLastOvernightError(Exception):
    pass


class CalendarExceptionMustHaveRealisticTimeAndDateError(Exception):
    pass


class BookingWindowMustBeInTheFutureError(Exception):
    pass


class InvalidWeekdayError(Exception):
    pass


class WorkingPeriodsOverlapError(Exception):
    pass


class WorkingPeriodsNotFoundError(Exception):
    pass


class InvalidReasonError(Exception):
    pass
