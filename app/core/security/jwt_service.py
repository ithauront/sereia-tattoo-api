from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import uuid4
from jose import jwt, JWTError
from pydantic import SecretStr

from app.core.exceptions.security import TokenError


class JWTService:
    def __init__(self, secret_key: SecretStr, algorithm: str):
        if secret_key is None:
            raise ValueError("SECRET_KEY must not be None")
        self.secret_key = secret_key.get_secret_value()
        self.algorithm = algorithm

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(timezone.utc)

    def create(
        self,
        subject: str,
        minutes: int,
        token_type: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        now = self._now_utc()

        payload: Dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=minutes)).timestamp()),
            "jti": str(uuid4()),
        }

        if extra_claims:
            payload.update(extra_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode(self, token: str) -> Dict[str, Any]:
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={"verify_exp": True},
        )

    def verify(self, token: str, expected_type: str) -> Dict[str, Any]:
        try:
            payload = self.decode(token)
        except JWTError as exc:
            raise TokenError("invalid_token") from exc

        if payload.get("type") != expected_type:
            raise TokenError("wrong_token_type")

        if not payload.get("sub"):
            raise TokenError("missing_sub")

        return payload
