from fastapi import Depends
from app.core.config import settings
from app.core.security.versioned_token_service import VersionedTokenService
from app.core.security.jwt_service import JWTService


def get_jwt_service() -> JWTService:
    return JWTService(secret_key=settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def get_activation_token_service(
    jwt_service: JWTService = Depends(get_jwt_service),
) -> VersionedTokenService:
    return VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )


def get_reset_password_token_service(
    jwt_service: JWTService = Depends(get_jwt_service),
) -> VersionedTokenService:
    return VersionedTokenService(
        jwt_service=jwt_service, token_type="reset_password", ttl_minutes=15
    )


def get_access_token_service(
    jwt_service: JWTService = Depends(get_jwt_service),
) -> VersionedTokenService:
    return VersionedTokenService(
        jwt_service=jwt_service,
        token_type="access",
        ttl_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def get_refresh_token_service(
    jwt_service: JWTService = Depends(get_jwt_service),
) -> VersionedTokenService:
    return VersionedTokenService(
        jwt_service=jwt_service,
        token_type="refresh",
        ttl_minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
    )
