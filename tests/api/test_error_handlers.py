import json

import pytest
from starlette.requests import Request

from app.api.error_handlers import domain_exception_handler
from app.core.exceptions.appointments import (
    AppointmentMustBeInCorrectPreviousStatusError,
    AppointmentNotFoundError,
    AppointmentProjectNotFoundError,
    AppointmentProjectRequiresAuthenticatedUserError,
    AppointmentProjectStateError,
    OnlyAdminOrOwnerOfAppointmentError,
    TotalSessionsExceededError,
    TotalSessionsMustBeAtLeastTwoError,
    TotalSessionsMustMatchProjectError,
)
from app.core.exceptions.security import TokenError
from app.core.exceptions.users import UserNotFoundError
from app.core.exceptions.validation import ValidationError


def make_request(route_name: str) -> Request:
    route = type("Route", (), {"name": route_name})()
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "route": route,
        }
    )


async def test_common_error_response_is_used_as_fallback():
    response = await domain_exception_handler(
        make_request("get_user"),
        AppointmentNotFoundError(),
    )

    assert response.status_code == 404
    assert json.loads(response.body) == {"detail": "appointment_not_found"}


async def test_route_specific_response_overrides_common_response():
    response = await domain_exception_handler(
        make_request("create_appointment"),
        UserNotFoundError(),
    )

    assert response.status_code == 400
    assert json.loads(response.body) == {"detail": "user_does_not_exists_or_is_inactive"}


async def test_dynamic_exception_detail_is_rendered():
    exception = ValidationError("invalid domain value")

    response = await domain_exception_handler(make_request("any_route"), exception)

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": "invalid domain value"}


async def test_invalid_project_size_uses_semantic_error_response():
    response = await domain_exception_handler(
        make_request("any_route"),
        TotalSessionsMustBeAtLeastTwoError(),
    )

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": "total_sessions_must_be_at_least_two"}


async def test_unmapped_exception_is_not_hidden():
    exception = RuntimeError("unexpected failure")

    with pytest.raises(RuntimeError, match="unexpected failure"):
        await domain_exception_handler(make_request("any_route"), exception)


@pytest.mark.parametrize(
    ("exception", "status_code", "detail"),
    [
        (AppointmentProjectNotFoundError(), 404, "project_not_found"),
        (
            AppointmentProjectRequiresAuthenticatedUserError(),
            403,
            "appointment_project_management_requires_authenticated_user",
        ),
        (TotalSessionsMustMatchProjectError(), 409, "total_sessions_does_not_match_project"),
        (TotalSessionsExceededError(), 409, "project_has_no_remaining_sessions"),
        (AppointmentProjectStateError(), 500, "project_is_broken"),
    ],
)
async def test_create_appointment_project_errors(exception, status_code, detail):
    response = await domain_exception_handler(make_request("create_appointment"), exception)

    assert response.status_code == status_code
    assert json.loads(response.body) == {"detail": detail}


async def test_refresh_token_error_uses_exception_text():
    response = await domain_exception_handler(
        make_request("refresh"), TokenError("token_revoked")
    )

    assert response.status_code == 401
    assert json.loads(response.body) == {"detail": "token_revoked"}


@pytest.mark.parametrize(
    ("exception", "status_code", "detail"),
    [
        (OnlyAdminOrOwnerOfAppointmentError(), 403, "unauthorized_user"),
        (
            AppointmentMustBeInCorrectPreviousStatusError(),
            409,
            "appointment_cannot_be_canceled_in_current_status",
        ),
        (ValidationError("text_required"), 422, "cancellation_reason_required"),
        (
            ValidationError("text_must_have_at_least_5_characters"),
            422,
            "cancellation_reason_must_have_at_least_5_characters",
        ),
        (
            ValidationError("text_must_contain_letters"),
            422,
            "cancellation_reason_must_contain_letters",
        ),
    ],
)
async def test_cancel_appointment_errors_have_route_specific_responses(
    exception, status_code, detail
):
    response = await domain_exception_handler(make_request("cancel_appointment"), exception)

    assert response.status_code == status_code
    assert json.loads(response.body) == {"detail": detail}
