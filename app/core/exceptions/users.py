class UserNotFoundError(Exception):
    pass


class UserActivatedBeforeError(Exception):
    pass


class UserAlreadyActivatedError(Exception):
    pass


class InvalidActivationTokenError(Exception):
    pass


class UsernameAlreadyTakenError(Exception):
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
