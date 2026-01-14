from fastapi import Depends, Header, HTTPException, status
from uuid import UUID

from app.api.dependencies.security import get_activation_token_service
from app.core.security.activation_context import ActivationContext
from app.core.security.activation_token_service import ActivationTokenService
from app.core.exceptions.security import TokenError


def get_current_activation_context(
    authorization: str = Header(..., alias="Authorization"),
    token_service: ActivationTokenService = Depends(get_activation_token_service),
) -> ActivationContext:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_authorization_header",
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = token_service.verify(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    return ActivationContext(
        user_id=UUID(payload["sub"]),
        token_version=payload["ver"],
    )
