from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from app.core.config import settings
from typing import Any, Dict

assert settings.SECRET_KEY is not None, "SECRET_KEY must be set in .env"
SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ALGORITHM = settings.JWT_ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_token(subject: str, minutes: int, token_type: str) -> str:
    now = _now_utc()
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


class TokenError(Exception):
    pass


def require_token(token: str, expected_type: str) -> Dict[str, Any]:
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise TokenError("invalid_token") from exc

    if payload.get("type") != expected_type:
        raise TokenError("wrong_token_type")

    if not payload.get("sub"):
        raise TokenError("missing_sub")

    return payload
