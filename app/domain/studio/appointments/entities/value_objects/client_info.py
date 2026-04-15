from dataclasses import dataclass
from uuid import UUID

from app.core.exceptions.clients import ClientInfoModelError


@dataclass(frozen=True)
class NonVipContact:
    name: str
    email: str
    phone: str


# TODO: fazer teste disso?
class ClientInfo:
    def __init__(
        self,
        *,
        vip_client_id: UUID | None = None,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ):
        if vip_client_id is None:
            if not (name and email and phone):
                raise ClientInfoModelError(
                    "Non_VIP_clients_must_provide_name_email_and_phone"
                )

        self.vip_client_id = vip_client_id
        self.name = name
        self.email = email
        self.phone = phone

    @property
    def is_vip(self) -> bool:
        return self.vip_client_id is not None

    def matches_vip(self, vip_client_id: UUID) -> bool:
        return self.vip_client_id == vip_client_id

    def try_get_contact_info(self) -> NonVipContact | None:
        if self.is_vip:
            return None

        assert self.name is not None
        assert self.email is not None
        assert self.phone is not None

        return NonVipContact(
            name=self.name,
            email=self.email,
            phone=self.phone,
        )

    def __eq__(self, other):
        if not isinstance(other, ClientInfo):
            return False

        return (
            self.vip_client_id == other.vip_client_id
            and self.name == other.name
            and self.email == other.email
            and self.phone == other.phone
        )
