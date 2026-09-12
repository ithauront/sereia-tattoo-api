from fastapi import status

from app.api.errors.types import ErrorResponse, error
from app.core.exceptions.appointments import (
    AppointmentClientContactInfoCorruptedError,
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentMustBeScheduledError,
    AppointmentNotFoundError,
    AppointmentProjectNotFoundError,
    AppointmentProjectRequiresAuthenticatedUserError,
    AppointmentProjectStateError,
    AppointmentWasNotFullyPaidError,
    OnlyAdminOrOwnerOfAppointmentError,
    PriceMustBeDefinedError,
    PriceMustBePositiveError,
    ReasonForCancelationMustBeProvidedError,
    SlotIsAlreadyOccupiedError,
    SlotIsNotAvailableError,
    TotalSessionsExceededError,
    TotalSessionsMustMatchProjectError,
)
from app.core.exceptions.calendar import (
    CannotFindWorkingPeriodsForThisUserError,
    UserIsNotWorkingInDesignatedTimeframeError,
)
from app.core.exceptions.clients import ClientInfoModelError
from app.core.exceptions.users import UserInactiveError, UserNotFoundError
from app.core.exceptions.validation import ValidationError


def cancellation_validation_detail(exception: Exception) -> str:
    validation_code = str(exception)
    return {
        "text_required": "cancellation_reason_required",
        "text_must_have_at_least_5_characters": (
            "cancellation_reason_must_have_at_least_5_characters"
        ),
        "text_must_contain_letters": "cancellation_reason_must_contain_letters",
    }.get(validation_code, validation_code)


APPOINTMENT_ROUTE_ERROR_RESPONSES: dict[str, dict[type[Exception], ErrorResponse]] = {
    "create_appointment": {
        CannotFindWorkingPeriodsForThisUserError: error(
            status.HTTP_400_BAD_REQUEST, "the_time_slot_required_is_not_available"
        ),
        UserIsNotWorkingInDesignatedTimeframeError: error(
            status.HTTP_400_BAD_REQUEST, "the_time_slot_required_is_not_available"
        ),
        SlotIsNotAvailableError: error(
            status.HTTP_400_BAD_REQUEST, "the_time_slot_required_is_not_available"
        ),
        UserInactiveError: error(status.HTTP_400_BAD_REQUEST, "user_does_not_exists_or_is_inactive"),
        UserNotFoundError: error(status.HTTP_400_BAD_REQUEST, "user_does_not_exists_or_is_inactive"),
        SlotIsAlreadyOccupiedError: error(
            status.HTTP_400_BAD_REQUEST, "the_time_slot_required_is_occupied"
        ),
        ClientInfoModelError: error(
            status.HTTP_422_UNPROCESSABLE_CONTENT, lambda exception: str(exception)
        ),
        AppointmentClientContactInfoCorruptedError: error(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "appointment_is_broken"
        ),
        AppointmentProjectNotFoundError: error(status.HTTP_404_NOT_FOUND, "project_not_found"),
        AppointmentProjectRequiresAuthenticatedUserError: error(
            status.HTTP_403_FORBIDDEN,
            "appointment_project_management_requires_authenticated_user",
        ),
        AppointmentProjectStateError: error(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "project_is_broken"
        ),
        TotalSessionsMustMatchProjectError: error(
            status.HTTP_409_CONFLICT, "total_sessions_does_not_match_project"
        ),
        TotalSessionsExceededError: error(
            status.HTTP_409_CONFLICT, "project_has_no_remaining_sessions"
        ),
    },
    "quote_appointment": {
        AppointmentNotFoundError: error(status.HTTP_404_NOT_FOUND, "appointment_not_found"),
        OnlyAdminOrOwnerOfAppointmentError: error(status.HTTP_403_FORBIDDEN, "unauthorized_user"),
        AppointmentMustBeInCorrectPreviousStatusError: error(
            status.HTTP_409_CONFLICT, "appointment_cannot_be_quoted_in_current_status"
        ),
        PriceMustBePositiveError: error(status.HTTP_400_BAD_REQUEST, "price_must_be_positive"),
        AppointmentClientContactInfoCorruptedError: error(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "appointment_is_broken"
        ),
        PriceMustBeDefinedError: error(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "appointment_is_broken"
        ),
        AppointmentProjectStateError: error(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "project_is_broken"
        ),
        TotalSessionsMustMatchProjectError: error(
            status.HTTP_409_CONFLICT, "total_sessions_does_not_match_project"
        ),
    },
    "complete_paid_appointment": {
        AppointmentMustBeScheduledError: error(
            status.HTTP_409_CONFLICT,
            "only_appointments_in_scheduled_status_can_be_completed",
        ),
        AppointmentNotFoundError: error(status.HTTP_404_NOT_FOUND, "appointment_not_found"),
        AppointmentWasNotFullyPaidError: error(
            status.HTTP_409_CONFLICT,
            "appointment_was_not_fully_paid_check_payments_and_possible_refunds",
        ),
    },
    "cancel_appointment": {
        OnlyAdminOrOwnerOfAppointmentError: error(
            status.HTTP_403_FORBIDDEN, "unauthorized_user"
        ),
        AppointmentMustBeInCorrectPreviousStatusError: error(
            status.HTTP_409_CONFLICT,
            "appointment_cannot_be_canceled_in_current_status",
        ),
        ValidationError: error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            cancellation_validation_detail,
        ),
        ReasonForCancelationMustBeProvidedError: error(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "cancellation_reason_required"
        ),
        AppointmentClientContactInfoCorruptedError: error(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "appointment_is_broken"
        ),
    },
}
