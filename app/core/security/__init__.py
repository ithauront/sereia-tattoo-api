from app.core.config import settings
from app.core.security.jwt_service import JWTService
from app.core.security.passwords import hash_password, verify_password

assert settings.SECRET_KEY is not None, "SECRET_KEY must be set in .env"

jwt_service = JWTService(
    secret_key=settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
)

__all__ = ["jwt_service", "hash_password", "verify_password"]
