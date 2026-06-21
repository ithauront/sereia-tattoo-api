class WorkingPeriodMustHaveRealisticTimeAndDateError(Exception):
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
