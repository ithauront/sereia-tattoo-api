from pydantic import SecretStr
from app.core.security.jwt_service import JWTService
from app.core.security.activation_token_service import ActivationTokenService


def test_activation_token_contains_user_id_and_version():
    jwt_service = JWTService(
        secret_key=SecretStr("test-secret"),
        algorithm="HS256",
    )
    service = ActivationTokenService(jwt_service=jwt_service)

    token = service.create("user-id-123", version=2)

    payload = service.verify(token)

    assert payload["sub"] == "user-id-123"
    assert payload["ver"] == 2
