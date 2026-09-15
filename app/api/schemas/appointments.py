from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.types.appointment_enums import AppointmentType


class CreateAppointmentRequest(BaseModel):
    appointment_type: AppointmentType
    user_id: UUID
    start_at: datetime
    end_at: datetime
    placement: str
    details: str
    total_sessions: int | None = Field(default=None, ge=2)
    project_id: UUID | None = None
    size: str | None
    color: bool

    vip_client_id: UUID | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    referral_code: str | None = None


class CreateAppointmentResponse(BaseModel):
    appointment_id: UUID
    project_id: UUID | None
    current_session: int | None
    total_sessions: int | None


class QuoteAppointmentRequest(BaseModel):
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    total_sessions: int | None = Field(default=None, ge=2)

    @field_validator("price", mode="before")
    @classmethod
    def normalize_price(cls, value):
        if isinstance(value, str):
            value = value.replace(",", ".")
        return value


class QuoteAppointmentResponse(BaseModel):
    appointment_id: UUID
    project_id: UUID | None
    current_session: int | None
    total_sessions: int | None


class CancelAppointmentRequest(BaseModel):
    reason: str
