class PaymentMustBeGreaterThanZeroError(Exception):
    pass


class VipClientIdIsRequiredError(Exception):
    pass


class DuplicateExternalReferenceError(Exception):
    pass


class PaymentWithoutAppointmentRequireDescriptionError(Exception):
    pass


class PaymentLinkToAppointmentIsCorruptedError(Exception):
    pass


class PaymentMustHaveDepositPurposeError(Exception):
    pass


class PaymentOfThisPurposeMustHaveAppointmentError(Exception):
    pass


class VipClientHasInsufficientCreditError(Exception):
    pass


class PaymentOfThisTypeDoesNotNeedAVipClient(Exception):
    pass


class IdempotencyKeyConflictError(Exception):
    pass


class PaymentAmountExceedsMaximumError(Exception):
    pass


class InvalidPaymentAmountError(Exception):
    pass


class PaymentAmountHasSubCentPrecisionError(Exception):
    pass


class PaymentConsumesZeroClientCreditsError(Exception):
    pass
