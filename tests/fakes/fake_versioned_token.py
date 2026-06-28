from typing import Any

from app.core.security.versioned_token_service import VersionedTokenService


class FakeVersionedTokenService(VersionedTokenService):
    def __init__(self) -> None:
        pass

    def create(self, user_id: str, version: int) -> str:
        return f"fake-token-{user_id}-{version}"

    def verify(self, token: str) -> dict[str, Any]:
        return {"sub": "fake-user-id", "ver": 1}
