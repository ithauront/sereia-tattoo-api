from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID as pyUUID

from app.infrastructure.sqlalchemy.base_class import Base
from sqlalchemy import Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.sqlalchemy.models.working_period import WorkingPeriodModel


class CalendarSettingsModel(Base):
    __tablename__ = "calendar_settings"

    user_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True,
    )

    booking_window_until: Mapped[date] = mapped_column(Date(), nullable=False)

    working_periods: Mapped[list["WorkingPeriodModel"]] = relationship(
        "WorkingPeriodModel",
        back_populates="calendar_settings",
        cascade="all, delete-orphan",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
