from typing import Dict
from app.core.exceptions.security import TokenError
from app.core.security.jwt_service import JWTService


class ActivationTokenService:
    def __init__(self, jwt_service: JWTService):
        self.jwt = jwt_service

    def create(self, user_id: str, version: int) -> str:
        return self.jwt.create(
            subject=user_id,
            minutes=15,
            token_type="activation",
            extra_claims={"ver": version},
        )

    def verify(self, token: str) -> Dict:
        payload = self.jwt.verify(token, expected_type="activation")
        token_version = payload.get("ver")

        if token_version is None:
            raise TokenError("missing_token_version")

        return payload
