from fastapi import status

from app.api.errors.types import ErrorResponse, error
from app.core.exceptions.appointments import (
    AppointmentClientInfoBreakingDomainRules,
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentNotFoundError,
    IncorrectAppointmentStatusError,
    PriceMustBeDefinedError,
)
from app.core.exceptions.marketing import CreditMustBePositiveError, ZeroCreditQuantityNotAllowedError
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
from app.core.exceptions.users import VipClientNotFoundError

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

PAYMENT_ROUTE_ERROR_RESPONSES = {"create_payment": PAYMENT_ERROR_RESPONSES}
