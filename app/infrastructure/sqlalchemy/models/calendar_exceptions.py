from datetime import datetime
from uuid import UUID as pyUUID
from uuid import uuid4

from app.core.types.calendar_enums import CalendarExceptionType
from app.infrastructure.sqlalchemy.base_class import Base
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class CalendarExceptionsModel(Base):
    __tablename__ = "calendar_exceptions"

    __table_args__ = (
        CheckConstraint(
            "end_at > start_at",
            name="check_calendar_exception_end_after_start",
        ),
    )

    id: Mapped[pyUUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    calendar_of_user: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    exception_type: Mapped[CalendarExceptionType] = mapped_column(
        Enum(CalendarExceptionType, name="calendar_exception_type_enum"), nullable=False
    )

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
