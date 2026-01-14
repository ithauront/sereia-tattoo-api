class UserNotFoundError(Exception):
    pass


class UserAlreadyActivatedError(Exception):
    pass


class InvalidActivationTokenError(Exception):
    pass


class UsernameAlreadyTakenError(Exception):
    pass
