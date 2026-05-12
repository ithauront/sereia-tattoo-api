from uuid import UUID

from pydantic import BaseModel


class AddClientCreditByAdminInput(BaseModel):
    vip_client_id: UUID
    quantity: int
    reason: str
    actor_id: UUID


class AddClientCreditByAdminOutput(BaseModel):
    before: int
    after: int
