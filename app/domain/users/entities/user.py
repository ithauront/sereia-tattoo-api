from datetime import datetime, timezone
from uuid import UUID, uuid4


class User:
    def __init__(
        self,
        id: UUID | None = None,
        username: str = "",
        email: str = "",
        hashed_password: str = "",
        is_admin: bool = False,
        is_active: bool = False,
        has_activated_once: bool = False,
        activation_token_version: int = 0,
        password_token_version: int = 0,
        access_token_version: int = 0,
        refresh_token_version: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        now = datetime.now(timezone.utc)
        self.id = id or uuid4()
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.is_admin = is_admin
        self.is_active = is_active
        self.has_activated_once = has_activated_once
        self.activation_token_version = activation_token_version
        self.password_token_version = password_token_version
        self.access_token_version = access_token_version
        self.refresh_token_version = refresh_token_version
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @classmethod
    def create_pending(cls, email: str) -> "User":
        return cls(
            email=email,
            is_active=False,
            is_admin=False,
            has_activated_once=False,
            activation_token_version=0,
            password_token_version=0,
        )

    def change_password(self, new_hashed_password):
        self.hashed_password = new_hashed_password
        self.bump_password_token()
        self.bump_access_token()
        self.bump_refresh_token()
        self._touch()

    def change_email(self, new_email):
        self.email = new_email
        self._touch()
        self.bump_access_token()
        self.bump_refresh_token()

    def activate(self) -> bool:
        if self.is_active:
            return False

        self.is_active = True
        self.has_activated_once = True
        self._touch()
        return True

    def deactivate(self) -> bool:
        if not self.is_active:
            return False

        self.is_active = False
        self._touch()
        self.bump_access_token()
        self.bump_refresh_token()
        return True

    def promote_to_admin(self) -> bool:
        if self.is_admin:
            return False

        self.is_admin = True
        self._touch()
        return True

    def demote_from_admin(self) -> bool:
        if not self.is_admin:
            return False

        self.is_admin = False
        self._touch()
        self.bump_access_token()
        return True

    def bump_activation_token(self):
        self.activation_token_version += 1
        self._touch()

    def bump_password_token(self):
        self.password_token_version += 1
        self._touch()

    def bump_access_token(self):
        self.access_token_version += 1
        self._touch()

    def bump_refresh_token(self):
        self.refresh_token_version += 1
        self._touch()

    def _touch(self):
        self.updated_at = datetime.now(timezone.utc)
