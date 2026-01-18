from typing import Dict
from app.core.exceptions.security import TokenError
from app.core.security.jwt_service import JWTService


class VersionedTokenService:
    def __init__(self, jwt_service: JWTService, token_type: str, ttl_minutes: int):
        self.jwt = jwt_service
        self.token_type = token_type
        self.ttl_minutes = ttl_minutes

    def create(self, user_id: str, version: int) -> str:
        return self.jwt.create(
            subject=user_id,
            minutes=self.ttl_minutes,
            token_type=self.token_type,
            extra_claims={"ver": version},
        )

    def verify(self, token: str) -> Dict:
        payload = self.jwt.verify(token, expected_type=self.token_type)
        token_version = payload.get("ver")

        if token_version is None:
            raise TokenError("missing_token_version")

        return payload
