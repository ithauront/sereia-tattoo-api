from decimal import Decimal

from app.domain.studio.finances.enums.payment_enums import PaymentMethodType
from app.infrastructure.sqlalchemy.base_class import Base
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum, ForeignKey, Numeric, String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[PaymentMethodType] = mapped_column(
        Enum(PaymentMethodType, name="payment_method_enum"), nullable=False
    )
    vip_client_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vip_client.id"),
        nullable=True,
        index=True,
    )
    appointment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment.id"),
        nullable=True,
        index=True,
    )
    external_reference: Mapped[str] = mapped_column(
        String(255), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
