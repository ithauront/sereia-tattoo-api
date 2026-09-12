from fastapi import status
from pydantic import ValidationError as PydanticValidationError

from app.api.errors.types import ErrorResponse, error
from app.core.exceptions.appointments import (
    AppointmentNotFoundError,
    TotalSessionsMustBeAtLeastTwoError,
)
from app.core.exceptions.users import (
    AuthenticationFailedError,
    UserNotFoundError,
    VipClientNotFoundError,
)
from app.core.exceptions.validation import ValidationError

COMMON_ERROR_RESPONSES: dict[type[Exception], ErrorResponse] = {
    UserNotFoundError: error(status.HTTP_404_NOT_FOUND, "user_not_found"),
    VipClientNotFoundError: error(status.HTTP_404_NOT_FOUND, "vip_client_not_found"),
    AppointmentNotFoundError: error(status.HTTP_404_NOT_FOUND, "appointment_not_found"),
    AuthenticationFailedError: error(status.HTTP_401_UNAUTHORIZED, "invalid_credentials"),
    PydanticValidationError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT, lambda exception: str(exception)
    ),
    ValidationError: error(status.HTTP_422_UNPROCESSABLE_CONTENT, lambda exception: str(exception)),
    TotalSessionsMustBeAtLeastTwoError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "total_sessions_must_be_at_least_two",
    ),
}
