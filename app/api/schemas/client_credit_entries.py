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


class ReverseClientCreditsRequest(BaseModel):
    reason: str
    vip_client_id: UUID


class ReverseClientCreditsResponse(BaseModel):
    vip_client_id: UUID
    original_credit_id: UUID
    reversed_credit_id: UUID
    total_credits_before: int
    total_credits_after: int
