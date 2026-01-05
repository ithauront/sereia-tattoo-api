from fastapi import Depends
from app.core.config import settings
from app.core.security.activation_token_service import ActivationTokenService
from app.core.security.jwt_service import JWTService


def get_jwt_service() -> JWTService:
    return JWTService(secret_key=settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def get_activation_token_service(
    jwt_service: JWTService = Depends(get_jwt_service),
) -> ActivationTokenService:
    return ActivationTokenService(jwt_service=jwt_service)
