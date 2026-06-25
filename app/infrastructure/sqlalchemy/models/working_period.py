from datetime import datetime, time
from typing import TYPE_CHECKING
from uuid import UUID as pyUUID
from uuid import uuid4

from app.infrastructure.sqlalchemy.base_class import Base
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.infrastructure.sqlalchemy.models.calendar_settings import CalendarSettingsModel


class WorkingPeriodModel(Base):
    __tablename__ = "working_periods"

    __table_args__ = (
        CheckConstraint(
            "end_at > start_at",
            name="check_working_period_end_after_start",
        ),
        CheckConstraint(
            "weekday BETWEEN 0 AND 6",
            name="check_valid_weekday",
        ),
        UniqueConstraint(
            "calendar_settings_user_id",
            "weekday",
            "start_at",
            "end_at",
            name="unique_working_period",
        ),
    )

    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    calendar_settings_user_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar_settings.user_id"),
        nullable=False,
        index=True,
    )

    weekday: Mapped[int] = mapped_column(Integer, nullable=False)

    start_at: Mapped[time] = mapped_column(Time(), nullable=False)

    end_at: Mapped[time] = mapped_column(Time(), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    calendar_settings: Mapped["CalendarSettingsModel"] = relationship(
        "CalendarSettingsModel",
        back_populates="working_periods",
    )
