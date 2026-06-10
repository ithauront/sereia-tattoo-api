from uuid import UUID

from pydantic import BaseModel


class ReverseClientCreditByAdminInput(BaseModel):
    vip_client_id: UUID
    credit_id: UUID
    reason: str
    actor_id: UUID


class ReverseClientCreditByAdminOutput(BaseModel):
    reversed_credit_id: UUID
    before: int
    after: int
