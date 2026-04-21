class AppointmentMustHaveRealisticTimeAndDateError(Exception):
    pass


class TotalSessionsNumberMustBePositiveError(Exception):
    pass


class TotalSessionsNumberMustBeDefineError(Exception):
    pass


class CurrentSessionMustBeLessThanTotalError(Exception):
    pass


class PriceMustBeDefinedError(Exception):
    pass


class PriceMustBePositiveError(Exception):
    pass


class AppointmentMustBeInCorrectPreviousStatusError(Exception):
    pass


class AppointmentMustBeScheduledError(Exception):
    pass


class AppointmentWasNotFullyPaidError(Exception):
    pass


class CurrentSessionMustBePositiveError(Exception):
    pass


class AppointmentStatusBreakingDomainRules(Exception):
    message: str

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
