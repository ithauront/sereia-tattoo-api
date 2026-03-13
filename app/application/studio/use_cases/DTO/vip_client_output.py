from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.studio.users.entities.vip_client import VipClient


class VipClientOutput(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    phone: str
    email: str
    client_code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, vip_client: VipClient):
        return cls(
            id=vip_client.id,
            first_name=vip_client.first_name,
            last_name=vip_client.last_name,
            phone=vip_client.phone,
            email=vip_client.email,
            client_code=vip_client.client_code.value,
            created_at=vip_client.created_at,
            updated_at=vip_client.updated_at,
        )
