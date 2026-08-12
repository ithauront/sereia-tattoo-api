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
    size: str | None
    color: bool

    vip_client_id: UUID | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None

    referral_code: str | None = None


class QuoteAppointmentRequest(BaseModel):
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    @field_validator("price", mode="before")
    @classmethod
    def normalize_price(cls, value):
        if isinstance(value, str):
            value = value.replace(",", ".")
        return value
