from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID as pyUUID

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.infrastructure.sqlalchemy.base_class import Base


class AppointmentModel(Base):
    __tablename__ = "appointments"

    __table_args__ = (
        CheckConstraint(
            """
            vip_client_id IS NOT NULL
            OR (
                client_name IS NOT NULL
                AND client_email IS NOT NULL
                AND client_phone IS NOT NULL
            )
            """,
            name="check_client_info_valid",
        ),
    )

    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status_enum"),
        nullable=False,
        index=True,
    )
    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType, name="appointment_type_enum"), nullable=False, index=True
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    placement: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    size: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    current_session: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_sessions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), index=True
    )
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    deposit_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    vip_client_id: Mapped[pyUUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    client_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    client_email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    client_phone: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )

    referral_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    is_posted_on_socials: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), index=True
    )
    observations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
