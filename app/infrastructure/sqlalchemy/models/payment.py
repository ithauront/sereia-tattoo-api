from datetime import datetime
from decimal import Decimal
from uuid import UUID as pyUUID
from uuid import uuid4

from app.core.types.payment_enums import PaymentMethodType
from app.infrastructure.sqlalchemy.base_class import Base
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[pyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[PaymentMethodType] = mapped_column(
        Enum(PaymentMethodType, name="payment_method_enum"), nullable=False
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
    external_reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True, unique=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
