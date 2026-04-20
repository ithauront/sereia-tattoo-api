
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ClientInfoFilter:
    vip_client_id: UUID | None = None
    email: str | None = None
    phone: str | None = None
