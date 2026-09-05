import json

import pytest
from starlette.requests import Request

from app.api.error_handlers import domain_exception_handler
from app.core.exceptions.appointments import AppointmentNotFoundError
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


async def test_unmapped_exception_is_not_hidden():
    exception = RuntimeError("unexpected failure")

    with pytest.raises(RuntimeError, match="unexpected failure"):
        await domain_exception_handler(make_request("any_route"), exception)
