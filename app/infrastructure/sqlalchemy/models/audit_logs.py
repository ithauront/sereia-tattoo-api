from datetime import datetime
from typing import Dict

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text

from app.core.types.audit_actor_type import AuditActorType
from app.infrastructure.sqlalchemy.base_class import Base
from uuid import uuid4, UUID as pyUUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class AuditLogsModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    entity_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    entity_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    action: Mapped[str] = mapped_column(String(250), nullable=False)

    actor_id: Mapped[pyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    actor_type: Mapped[AuditActorType] = mapped_column(
        Enum(AuditActorType),
        nullable=False,
        index=True,
    )

    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    changes: Mapped[Dict | None] = mapped_column(JSON, nullable=True)

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
