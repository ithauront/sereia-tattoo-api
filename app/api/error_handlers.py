from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.errors.appointments import APPOINTMENT_ROUTE_ERROR_RESPONSES
from app.api.errors.common import COMMON_ERROR_RESPONSES
from app.api.errors.credits import CREDIT_ROUTE_ERROR_RESPONSES
from app.api.errors.payments import PAYMENT_ERROR_RESPONSES, PAYMENT_ROUTE_ERROR_RESPONSES
from app.api.errors.types import ErrorResponse
from app.api.errors.users import USER_ROUTE_ERROR_RESPONSES

__all__ = [
    "PAYMENT_ERROR_RESPONSES",
    "domain_exception_handler",
    "register_error_handlers",
]

ROUTE_ERROR_RESPONSES: dict[str, dict[type[Exception], ErrorResponse]] = {
    **APPOINTMENT_ROUTE_ERROR_RESPONSES,
    **PAYMENT_ROUTE_ERROR_RESPONSES,
    **CREDIT_ROUTE_ERROR_RESPONSES,
    **USER_ROUTE_ERROR_RESPONSES,
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
