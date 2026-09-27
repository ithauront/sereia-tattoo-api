from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions.appointments import AppointmentMustHaveRealisticTimeAndDateError
from app.core.types.appointment_enums import AppointmentStatus
from app.domain.studio.users.entities.user import User


@dataclass(frozen=True)
class RescheduleAppointmentInput:
    appointment_id: UUID
    start_at: datetime
    end_at: datetime
    actor: User
    override_deposit_retention: bool = False
    deposit_override_reason: str | None = None

    def __post_init__(self) -> None:
        _normalize_interval_to_utc(self)


@dataclass(frozen=True)
class RescheduleAppointmentOutput:
    appointment_id: UUID
    start_at: datetime
    end_at: datetime
    status: AppointmentStatus
    was_deposit_retained: bool
    deposit_override_applied: bool

    def __post_init__(self) -> None:
        _normalize_interval_to_utc(self)


def _normalize_interval_to_utc(
    dto: RescheduleAppointmentInput | RescheduleAppointmentOutput,
) -> None:
    for field in ("start_at", "end_at"):
        value = getattr(dto, field)
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise AppointmentMustHaveRealisticTimeAndDateError()
        object.__setattr__(dto, field, value.astimezone(timezone.utc))
