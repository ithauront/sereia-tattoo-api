class UserNotFoundError(Exception):
    pass


class VipClientNotFoundError(Exception):
    pass


class UserActivatedBeforeError(Exception):
    pass


class InvalidActivationTokenError(Exception):
    pass


class InvalidPasswordTokenError(Exception):
    pass


class UsernameAlreadyTakenError(Exception):
    pass


class EmailAlreadyTakenError(Exception):
    pass


class PhoneAlreadyTakenError(Exception):
    pass


class ClientCodeAlreadyTakenError(Exception):
    pass


class AuthenticationFailedError(Exception):
    pass


class UserInactiveError(Exception):
    pass


class CannotDemoteYourselfError(Exception):
    pass


class LastAdminCannotBeDemotedError(Exception):
    pass


class CannotDeactivateYourselfError(Exception):
    pass


class LastAdminCannotBeDeactivatedError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class AllClientCodesTakenError(Exception):
    pass
