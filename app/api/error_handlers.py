from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions.appointments import (
    AppointmentClientContactInfoCorruptedError,
    AppointmentClientInfoBreakingDomainRules,
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentMustBeScheduledError,
    AppointmentNotFoundError,
    AppointmentWasNotFullyPaidError,
    IncorrectAppointmentStatusError,
    OnlyAdminOrOwnerOfAppointmentError,
    PriceMustBeDefinedError,
    PriceMustBePositiveError,
    SlotIsAlreadyOccupiedError,
    SlotIsNotAvailableError,
)
from app.core.exceptions.calendar import (
    CannotFindWorkingPeriodsForThisUserError,
    UserIsNotWorkingInDesignatedTimeframeError,
)
from app.core.exceptions.clients import ClientInfoModelError
from app.core.exceptions.marketing import (
    CannotReverseNegativeEntryError,
    CreditAlreadyReversedError,
    CreditEntryNotFoundError,
    CreditMustBePositiveError,
    ZeroCreditQuantityNotAllowedError,
)
from app.core.exceptions.payment import (
    DuplicateExternalReferenceError,
    IdempotencyKeyConflictError,
    InvalidPaymentAmountError,
    PaymentAmountExceedsMaximumError,
    PaymentAmountHasSubCentPrecisionError,
    PaymentConsumesZeroClientCreditsError,
    PaymentLinkToAppointmentIsCorruptedError,
    PaymentMustBeGreaterThanZeroError,
    PaymentMustHaveDepositPurposeError,
    PaymentOfThisPurposeMustHaveAppointmentError,
    PaymentOfThisTypeDoesNotNeedAVipClient,
    PaymentWithoutAppointmentRequireDescriptionError,
    VipClientHasInsufficientCreditError,
    VipClientIdIsRequiredError,
)
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
    VipClientNotFoundError,
)
from app.core.exceptions.validation import ValidationError

DetailFactory = Callable[[Exception], Any]


@dataclass(frozen=True)
class ErrorResponse:
    status_code: int
    detail: Any | DetailFactory

    def render_detail(self, exception: Exception) -> Any:
        return self.detail(exception) if callable(self.detail) else self.detail


def error(status_code: int, detail: Any | DetailFactory) -> ErrorResponse:
    return ErrorResponse(status_code=status_code, detail=detail)


COMMON_ERROR_RESPONSES: dict[type[Exception], ErrorResponse] = {
    UserNotFoundError: error(status.HTTP_404_NOT_FOUND, "user_not_found"),
    VipClientNotFoundError: error(status.HTTP_404_NOT_FOUND, "vip_client_not_found"),
    AppointmentNotFoundError: error(status.HTTP_404_NOT_FOUND, "appointment_not_found"),
    AuthenticationFailedError: error(status.HTTP_401_UNAUTHORIZED, "invalid_credentials"),
    PydanticValidationError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT, lambda exception: str(exception)
    ),
    ValidationError: error(status.HTTP_422_UNPROCESSABLE_CONTENT, lambda exception: str(exception)),
}


PAYMENT_ERROR_RESPONSES: dict[type[Exception], ErrorResponse] = {
    AppointmentNotFoundError: error(status.HTTP_404_NOT_FOUND, "appointment_not_found"),
    VipClientNotFoundError: error(status.HTTP_404_NOT_FOUND, "vip_client_not_found"),
    DuplicateExternalReferenceError: error(
        status.HTTP_409_CONFLICT, "external_reference_already_exists"
    ),
    IdempotencyKeyConflictError: error(status.HTTP_409_CONFLICT, "idempotency_key_conflict"),
    IncorrectAppointmentStatusError: error(
        status.HTTP_409_CONFLICT, "appointment_cannot_accept_deposit_in_current_status"
    ),
    AppointmentMustBeInCorrectPreviousStatusError: error(
        status.HTTP_409_CONFLICT, "appointment_cannot_accept_deposit_in_current_status"
    ),
    VipClientHasInsufficientCreditError: error(
        status.HTTP_409_CONFLICT, "vip_client_has_insufficient_credit"
    ),
    PaymentOfThisTypeDoesNotNeedAVipClient: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "credit_owner_is_only_allowed_for_client_credit_payments",
    ),
    PaymentOfThisPurposeMustHaveAppointmentError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "appointment_id_is_required_for_this_payment_purpose",
    ),
    VipClientIdIsRequiredError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "credit_owner_vip_client_id_is_required"
    ),
    PaymentWithoutAppointmentRequireDescriptionError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "description_is_required_when_appointment_id_is_not_provided",
    ),
    PaymentConsumesZeroClientCreditsError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "client_credit_payment_must_consume_at_least_one_credit",
    ),
    PaymentMustBeGreaterThanZeroError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "payment_amount_must_be_greater_than_zero"
    ),
    PaymentAmountExceedsMaximumError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "payment_amount_exceeds_maximum"
    ),
    PaymentAmountHasSubCentPrecisionError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "payment_amount_must_have_at_most_two_decimal_places",
    ),
    InvalidPaymentAmountError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "payment_amount_must_be_finite"
    ),
    AppointmentClientInfoBreakingDomainRules: error(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "appointment_data_is_inconsistent"
    ),
    PriceMustBeDefinedError: error(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "appointment_data_is_inconsistent"
    ),
    PaymentLinkToAppointmentIsCorruptedError: error(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "payment_data_is_inconsistent"
    ),
    PaymentMustHaveDepositPurposeError: error(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "payment_data_is_inconsistent"
    ),
    CreditMustBePositiveError: error(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "client_credit_data_is_inconsistent"
    ),
    ZeroCreditQuantityNotAllowedError: error(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "client_credit_data_is_inconsistent"
    ),
}


ROUTE_ERROR_RESPONSES: dict[str, dict[type[Exception], ErrorResponse]] = {
    "create_payment": PAYMENT_ERROR_RESPONSES,
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
        PriceMustBeDefinedError: error(status.HTTP_500_INTERNAL_SERVER_ERROR, "appointment_is_broken"),
    },
    "complete_paid_appointment": {
        AppointmentMustBeScheduledError: error(
            status.HTTP_409_CONFLICT, "only_appointments_in_scheduled_status_can_be_completed"
        ),
        AppointmentNotFoundError: error(status.HTTP_404_NOT_FOUND, "appointment_not_found"),
        AppointmentWasNotFullyPaidError: error(
            status.HTTP_409_CONFLICT,
            "appointment_was_not_fully_paid_check_payments_and_possible_refunds",
        ),
    },
    "reverse_client_credits_by_admin": {
        VipClientNotFoundError: error(status.HTTP_404_NOT_FOUND, "vip_client_not_found"),
        CannotReverseNegativeEntryError: error(
            status.HTTP_400_BAD_REQUEST,
            {
                "code": "cannot_reverse_negative_credit",
                "message": "This credit is negative and cannot be reversed.",
                "hint": "Create an opposite credit entry and provide a reason and related_entry_id.",
            },
        ),
        CreditAlreadyReversedError: error(
            status.HTTP_400_BAD_REQUEST, "credit_was_already_reversed_before"
        ),
        CreditEntryNotFoundError: error(status.HTTP_404_NOT_FOUND, "credit_not_found"),
    },
    "add_client_credits_by_admin": {
        CreditMustBePositiveError: error(status.HTTP_400_BAD_REQUEST, "invalid_credit_quantity"),
    },
    "get_credit_entry_by_id": {
        CreditEntryNotFoundError: error(status.HTTP_404_NOT_FOUND, "client_credit_entry_not_found"),
        UserNotFoundError: error(
            status.HTTP_404_NOT_FOUND, "credit_came_from_an_admin_operation_but_admin_not_found"
        ),
        VipClientNotFoundError: error(
            status.HTTP_404_NOT_FOUND, "client_credit_entry_in_not_attached_to_a_vip_client"
        ),
    },
    "first_activation": {
        UserActivatedBeforeError: error(status.HTTP_409_CONFLICT, "user_was_activated_before"),
        InvalidActivationTokenError: error(status.HTTP_401_UNAUTHORIZED, "invalid_activation_token"),
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
        InvalidPasswordTokenError: error(status.HTTP_401_UNAUTHORIZED, "invalid_activation_token"),
    },
    "login": {
        UserInactiveError: error(status.HTTP_403_FORBIDDEN, "inactive_user"),
    },
    "refresh": {
        TokenError: error(status.HTTP_401_UNAUTHORIZED, lambda exception: exception.message),
    },
    "resend_email": {
        UserActivatedBeforeError: error(status.HTTP_409_CONFLICT, "user_has_been_activated_before"),
    },
    "create_user": {
        UserAlreadyExistsError: error(status.HTTP_409_CONFLICT, "user_already_exists"),
    },
    "deactivate_user": {
        LastAdminCannotBeDeactivatedError: error(
            status.HTTP_409_CONFLICT, "last_admin_cannot_be_deactivated"
        ),
        CannotDeactivateYourselfError: error(status.HTTP_409_CONFLICT, "cannot_deactivate_yourself"),
    },
    "demote_user": {
        LastAdminCannotBeDemotedError: error(status.HTTP_409_CONFLICT, "last_admin_cannot_be_demoted"),
        CannotDemoteYourselfError: error(status.HTTP_409_CONFLICT, "cannot_demote_yourself"),
    },
    "generate_vip_client_code_suggestions": {
        AllClientCodesTakenError: error(
            status.HTTP_409_CONFLICT, "please_try_creating_client_code_with_last_name"
        ),
    },
    "create_vip_client": {
        EmailAlreadyTakenError: error(status.HTTP_409_CONFLICT, "email_already_taken"),
        PhoneAlreadyTakenError: error(status.HTTP_409_CONFLICT, "phone_already_taken"),
        ClientCodeAlreadyTakenError: error(
            status.HTTP_409_CONFLICT, "client_code_already_taken_please_generate_another"
        ),
    },
    "change_vip_client_email": {
        EmailAlreadyTakenError: error(status.HTTP_409_CONFLICT, "email_chosen_is_already_taken"),
    },
    "change_vip_client_phone": {
        PhoneAlreadyTakenError: error(status.HTTP_409_CONFLICT, "phone_chosen_is_already_taken"),
    },
}


async def domain_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    route = request.scope.get("route")
    route_name = getattr(route, "name", "")
    response = ROUTE_ERROR_RESPONSES.get(route_name, {}).get(type(exception))
    response = response or COMMON_ERROR_RESPONSES.get(type(exception))
    if response is None:
        raise exception
    return JSONResponse(
        status_code=response.status_code,
        content={"detail": response.render_detail(exception)},
    )


def register_error_handlers(app: FastAPI) -> None:
    exception_types = set(COMMON_ERROR_RESPONSES)
    for responses in ROUTE_ERROR_RESPONSES.values():
        exception_types.update(responses)
    for exception_type in exception_types:
        app.add_exception_handler(exception_type, domain_exception_handler)
