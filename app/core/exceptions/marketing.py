class ZeroCreditQuantityNotAllowedError(Exception):
    pass


class CreditMustBePositiveError(Exception):
    pass


class CreditEntryNotFoundError(Exception):
    pass


class CannotReverseNegativeEntryError(Exception):
    pass


class CreditAlreadyReversedError(Exception):
    pass
