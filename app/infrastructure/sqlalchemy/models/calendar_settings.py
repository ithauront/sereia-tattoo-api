from datetime import date, datetime
from uuid import UUID as pyUUID

from app.infrastructure.sqlalchemy.base_class import Base
from app.infrastructure.sqlalchemy.models.working_period import WorkingPeriodModel
from sqlalchemy import Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class CalendarSettingsModel(Base):
    __tablename__ = "calendar_settings"

    user_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True,
    )

    booking_window_until: Mapped[date] = mapped_column(Date(), nullable=False)

    working_periods: Mapped[list["WorkingPeriodModel"]] = relationship(
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
