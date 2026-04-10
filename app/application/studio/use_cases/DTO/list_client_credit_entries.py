from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.marketing.entities.client_credit_entry import ClientCreditEntry


class ListCreditEntriesByClientIdInput(BaseModel):
    vip_client_id: UUID
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)
    direction: Direction = Direction.asc


class CreditEntryOutput(BaseModel):
    id: UUID
    quantity: int
    source_type: str
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(cls, credit_entry: ClientCreditEntry):
        return cls(
            id=credit_entry.id,
            quantity=credit_entry.quantity,
            source_type=credit_entry.source_type.value,
            reason=credit_entry.reason,
            created_at=credit_entry.created_at,
        )


class ListCreditEntriesOutput(BaseModel):
    entries: list[CreditEntryOutput]
    total: int
    page: int
    limit: int
