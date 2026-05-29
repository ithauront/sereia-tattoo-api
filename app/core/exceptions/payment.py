class PaymentMustBeGreaterThanZeroError(Exception):
    pass


class VipClientIdIsRequiredError(Exception):
    pass


class DuplicateExternalReferenceError(Exception):
    pass


class PaymentWithoutAppointmentRequireDescriptionError(Exception):
    pass
