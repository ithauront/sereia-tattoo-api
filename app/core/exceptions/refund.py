class RefundMustBeGreaterThanZeroError(Exception):
    pass


class VipClientIdIsRequiredForCreditRefundError(Exception):
    pass


class RefundsWithoutAppointmentRequireReasonError(Exception):
    pass
