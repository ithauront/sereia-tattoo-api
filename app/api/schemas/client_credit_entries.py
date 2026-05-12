from uuid import UUID

from pydantic import BaseModel


class AddClientCreditsResponse(BaseModel):
    vip_client: UUID
    quantity_added: int
    total_credits_before: int
    total_credits_after: int


class AddClientCreditsRequest(BaseModel):
    quantity: int
    reason: str
