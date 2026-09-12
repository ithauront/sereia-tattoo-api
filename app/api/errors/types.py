from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

DetailFactory = Callable[[Exception], Any]


@dataclass(frozen=True)
class ErrorResponse:
    status_code: int
    detail: Any | DetailFactory

    def render_detail(self, exception: Exception) -> Any:
        return self.detail(exception) if callable(self.detail) else self.detail


def error(status_code: int, detail: Any | DetailFactory) -> ErrorResponse:
    return ErrorResponse(status_code=status_code, detail=detail)
