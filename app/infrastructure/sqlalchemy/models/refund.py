from decimal import Decimal
from uuid import uuid4, UUID as pyUUID
from sqlalchemy import Enum, ForeignKey, Numeric, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types.refund_enums import RefundMethodType, RefundStatus
from app.infrastructure.sqlalchemy.base_class import Base
from datetime import datetime


class RefundModel(Base):
    __tablename__ = "refunds"

    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    refund_status: Mapped[RefundStatus] = mapped_column(
        Enum(RefundStatus, name="refund_status_enum"), nullable=False
    )
    refund_method: Mapped[RefundMethodType] = mapped_column(
        Enum(RefundMethodType, name="refund_method_enum"), nullable=False
    )
    vip_client_id: Mapped[pyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vip_client.id"),
        nullable=True,
        index=True,
    )
    appointment_id: Mapped[pyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id"),
        nullable=True,
        index=True,
    )
    payment_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id"),
        nullable=False,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
