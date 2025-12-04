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
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def change_password(self, new_hashed_password):
        self.hashed_password = new_hashed_password
        self._touch()

    def activate(self):
        if not self.is_active:
            self.is_active = True
            self._touch()

    def deactivate(self):
        if self.is_active:
            self.is_active = False
            self._touch()

    def promote_to_admin(self):
        if not self.is_admin:
            self.is_admin = True
            self._touch()

    def demote_from_admin(self):
        if self.is_admin:
            self.is_admin = False
            self._touch()

    def _touch(self):
        self.updated_at = datetime.now(timezone.utc)
