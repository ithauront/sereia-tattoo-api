from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum, ForeignKey, Integer, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.domain.studio.marketing.enums.client_credit_source_type import (
    ClientCreditSourceType,
)
from app.infrastructure.sqlalchemy.base_class import Base


class ClientCreditEntryModel(Base):
    __tablename__ = "client_credit_entry"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    vip_client_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vip_client.id"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    source_type: Mapped[ClientCreditSourceType] = mapped_column(
        Enum(ClientCreditSourceType, name="client_credit_source_type"), nullable=False
    )
    related_entry_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("client_credit_entry.id"),
        nullable=True,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
