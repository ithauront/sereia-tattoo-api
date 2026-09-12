from fastapi import status

from app.api.errors.types import ErrorResponse, error
from app.core.exceptions.marketing import (
    CannotReverseNegativeEntryError,
    CreditAlreadyReversedError,
    CreditEntryNotFoundError,
    CreditMustBePositiveError,
)
from app.core.exceptions.users import UserNotFoundError, VipClientNotFoundError

CREDIT_ROUTE_ERROR_RESPONSES: dict[str, dict[type[Exception], ErrorResponse]] = {
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
        CreditEntryNotFoundError: error(
            status.HTTP_404_NOT_FOUND, "client_credit_entry_not_found"
        ),
        UserNotFoundError: error(
            status.HTTP_404_NOT_FOUND,
            "credit_came_from_an_admin_operation_but_admin_not_found",
        ),
        VipClientNotFoundError: error(
            status.HTTP_404_NOT_FOUND,
            "client_credit_entry_in_not_attached_to_a_vip_client",
        ),
    },
}
