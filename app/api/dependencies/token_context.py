from typing import Callable, Type
from fastapi import Depends, Header, HTTPException, status
from uuid import UUID

from app.api.dependencies.security import (
    get_activation_token_service,
    get_reset_password_token_service,
)
from app.core.exceptions.security import TokenError
from app.core.security.activation_context import ActivationContext
from app.core.security.base_token_context import BaseTokenContext
from app.core.security.reset_password_context import ResetPasswordContext
from app.core.security.versioned_token_service import VersionedTokenService


def token_context_dependency(
    *,
    token_service_dep,
    context_class: Type[BaseTokenContext],
) -> Callable:
    def dependency(
        authorization: str = Header(...),
        token_service: VersionedTokenService = Depends(token_service_dep),
    ):
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_credentials",
            )

        token = authorization.removeprefix("Bearer ").strip()

        try:
            payload = token_service.verify(token)
            user_id = UUID(payload["sub"])
        except (TokenError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_credentials",
            )

        return context_class(
            user_id=user_id,
            token_version=payload["ver"],
        )

    return dependency


get_current_activation_context = token_context_dependency(
    token_service_dep=get_activation_token_service,
    context_class=ActivationContext,
)

get_current_reset_password_context = token_context_dependency(
    token_service_dep=get_reset_password_token_service,
    context_class=ResetPasswordContext,
)
