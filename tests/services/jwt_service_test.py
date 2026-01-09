from pydantic import SecretStr
import pytest
from app.core.exceptions.security import TokenError
from app.core.security.jwt_service import JWTService


def test_create_and_decode_token():
    service = JWTService(secret_key=SecretStr("secret"), algorithm="HS256")

    token = service.create(
        subject="user-id",
        minutes=10,
        token_type="access",
    )

    payload = service.decode(token)

    assert payload["sub"] == "user-id"
    assert payload["type"] == "access"


def test_verify_accepts_correct_type():
    service = JWTService(SecretStr("secret"), "HS256")

    token = service.create("user-id", 10, "access")

    payload = service.verify(token, expected_type="access")

    assert payload["sub"] == "user-id"


def test_verify_rejects_wrong_type():
    service = JWTService(SecretStr("secret"), "HS256")

    token = service.create("user-id", 10, "refresh")

    with pytest.raises(TokenError, match="wrong_token_type"):
        service.verify(token, expected_type="access")


def test_verify_rejects_missing_sub():
    service = JWTService(SecretStr("secret"), "HS256")

    token = service.create(
        subject="",
        minutes=10,
        token_type="access",
    )

    with pytest.raises(TokenError, match="missing_sub"):
        service.verify(token, expected_type="access")


def test_verify_rejects_expired_token():
    service = JWTService(SecretStr("secret"), "HS256")

    token = service.create("user-id", minutes=-1, token_type="access")

    with pytest.raises(TokenError, match="invalid_token"):
        service.verify(token, expected_type="access")


def test_extra_claims_are_preserved():
    service = JWTService(SecretStr("secret"), "HS256")

    token = service.create(
        subject="user-id",
        minutes=10,
        token_type="activation",
        extra_claims={"version": 2},
    )

    payload = service.verify(token, expected_type="activation")

    assert payload["version"] == 2
