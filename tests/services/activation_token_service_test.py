from freezegun import freeze_time
from pydantic import SecretStr
import pytest
from app.core.exceptions.security import TokenError
from app.core.security.jwt_service import JWTService
from app.core.security.versioned_token_service import VersionedTokenService


def test_activation_token_contains_user_id_and_version():
    jwt_service = JWTService(
        secret_key=SecretStr("test-secret"),
        algorithm="HS256",
    )
    service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )

    token = service.create("user-id-123", version=2)

    payload = service.verify(token)

    assert payload["sub"] == "user-id-123"
    assert payload["ver"] == 2


def test_reset_password_token_is_rejected_by_activation_service():
    jwt_service = JWTService(
        secret_key=SecretStr("test-secret"),
        algorithm="HS256",
    )

    reset_password_service = VersionedTokenService(
        jwt_service=jwt_service,
        token_type="reset_password",
        ttl_minutes=15,
    )

    activation_service = VersionedTokenService(
        jwt_service=jwt_service,
        token_type="activation",
        ttl_minutes=15,
    )

    token = reset_password_service.create("user-id-123", version=1)

    with pytest.raises(TokenError, match="wrong_token_type"):
        activation_service.verify(token)


def test_activation_token_expired():
    jwt_service = JWTService(
        secret_key=SecretStr("test-secret"),
        algorithm="HS256",
    )
    service = VersionedTokenService(
        jwt_service=jwt_service, token_type="activation", ttl_minutes=15
    )

    with freeze_time("2025-01-01 12:00:00"):
        token = service.create("user-id-123", version=1)

    with freeze_time("2025-01-01 12:16:00"):
        with pytest.raises(TokenError):
            service.verify(token)
