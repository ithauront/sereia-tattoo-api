from fastapi import status

from app.api.errors.types import ErrorResponse, error
from app.core.exceptions.security import TokenError
from app.core.exceptions.users import (
    AllClientCodesTakenError,
    AuthenticationFailedError,
    CannotDeactivateYourselfError,
    CannotDemoteYourselfError,
    ClientCodeAlreadyTakenError,
    EmailAlreadyTakenError,
    InvalidActivationTokenError,
    InvalidPasswordTokenError,
    LastAdminCannotBeDeactivatedError,
    LastAdminCannotBeDemotedError,
    PhoneAlreadyTakenError,
    UserActivatedBeforeError,
    UserAlreadyExistsError,
    UserInactiveError,
    UsernameAlreadyTakenError,
    UserNotFoundError,
)

USER_ROUTE_ERROR_RESPONSES: dict[str, dict[type[Exception], ErrorResponse]] = {
    "first_activation": {
        UserActivatedBeforeError: error(status.HTTP_409_CONFLICT, "user_was_activated_before"),
        InvalidActivationTokenError: error(
            status.HTTP_401_UNAUTHORIZED, "invalid_activation_token"
        ),
        UsernameAlreadyTakenError: error(status.HTTP_409_CONFLICT, "username_already_taken"),
    },
    "change_password": {
        UserNotFoundError: error(status.HTTP_401_UNAUTHORIZED, "invalid_credentials"),
        AuthenticationFailedError: error(status.HTTP_401_UNAUTHORIZED, "invalid_credentials"),
    },
    "change_email": {
        UserNotFoundError: error(status.HTTP_403_FORBIDDEN, "invalid_credentials"),
        AuthenticationFailedError: error(status.HTTP_403_FORBIDDEN, "invalid_credentials"),
        EmailAlreadyTakenError: error(status.HTTP_409_CONFLICT, "email_chosen_is_already_taken"),
    },
    "reset_password": {
        UserInactiveError: error(status.HTTP_409_CONFLICT, "user_inactive"),
        InvalidPasswordTokenError: error(
            status.HTTP_401_UNAUTHORIZED, "invalid_activation_token"
        ),
    },
    "login": {UserInactiveError: error(status.HTTP_403_FORBIDDEN, "inactive_user")},
    "refresh": {
        TokenError: error(status.HTTP_401_UNAUTHORIZED, lambda exception: str(exception))
    },
    "resend_email": {
        UserActivatedBeforeError: error(
            status.HTTP_409_CONFLICT, "user_has_been_activated_before"
        )
    },
    "create_user": {
        UserAlreadyExistsError: error(status.HTTP_409_CONFLICT, "user_already_exists")
    },
    "deactivate_user": {
        LastAdminCannotBeDeactivatedError: error(
            status.HTTP_409_CONFLICT, "last_admin_cannot_be_deactivated"
        ),
        CannotDeactivateYourselfError: error(
            status.HTTP_409_CONFLICT, "cannot_deactivate_yourself"
        ),
    },
    "demote_user": {
        LastAdminCannotBeDemotedError: error(
            status.HTTP_409_CONFLICT, "last_admin_cannot_be_demoted"
        ),
        CannotDemoteYourselfError: error(status.HTTP_409_CONFLICT, "cannot_demote_yourself"),
    },
    "generate_vip_client_code_suggestions": {
        AllClientCodesTakenError: error(
            status.HTTP_409_CONFLICT, "please_try_creating_client_code_with_last_name"
        )
    },
    "create_vip_client": {
        EmailAlreadyTakenError: error(status.HTTP_409_CONFLICT, "email_already_taken"),
        PhoneAlreadyTakenError: error(status.HTTP_409_CONFLICT, "phone_already_taken"),
        ClientCodeAlreadyTakenError: error(
            status.HTTP_409_CONFLICT, "client_code_already_taken_please_generate_another"
        ),
    },
    "change_vip_client_email": {
        EmailAlreadyTakenError: error(status.HTTP_409_CONFLICT, "email_chosen_is_already_taken")
    },
    "change_vip_client_phone": {
        PhoneAlreadyTakenError: error(status.HTTP_409_CONFLICT, "phone_chosen_is_already_taken")
    },
}
