from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry


class GetCreditEntryDetailsByIdInput(BaseModel):
    client_credit_id: UUID


class CreditEntryDetailsOutput(BaseModel):
    id: UUID
    vip_client_name: str
    source_id: UUID
    admin_name: str | None = None
    related_entry_id: UUID | None
    quantity: int
    source_type: str
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_entity(
        cls,
        *,
        credit_entry: ClientCreditEntry,
        vip_client_name: str,
        admin_name: str | None,
    ):
        return cls(
            id=credit_entry.id,
            vip_client_name=vip_client_name,
            source_id=credit_entry.source_id,
            admin_name=admin_name,
            related_entry_id=credit_entry.related_entry_id,
            quantity=credit_entry.quantity,
            source_type=credit_entry.source_type.value,
            reason=credit_entry.reason,
            created_at=credit_entry.created_at,
        )
