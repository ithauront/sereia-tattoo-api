from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.domain.studio.users.entities.value_objects.client_code import ClientCode


class VipClient:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        client_code: ClientCode,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        now = datetime.now(timezone.utc)
        self.id = id or uuid4()
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.client_code = client_code
        self.created_at = created_at or now
        self._updated_at = updated_at or now

    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        client_code: ClientCode,
    ) -> "VipClient":
        return cls(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            client_code=client_code,
        )

    def change_email(self, new_email: str):
        self.email = new_email
        self._touch()

    def change_phone(self, new_phone: str):
        self.phone = new_phone
        self._touch()

    @property
    def updated_at(self):
        return self._updated_at

    def _touch(self):
        self._updated_at = datetime.now(timezone.utc)
