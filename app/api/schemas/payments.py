from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.types.payment_enums import PaymentMethodType, PaymentPurposeType


class CreatePaymentRequest(BaseModel):
    idempotency_key: UUID
    payment_method: PaymentMethodType
    payment_purpose: PaymentPurposeType
    appointment_id: UUID | None = None
    credit_owner_vip_client_id: UUID | None = None
    description: str | None = None
    external_reference: str | None = Field(default=None, max_length=255)

    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    @field_validator("amount", mode="before")
    @classmethod
    def normalize_price(cls, value):
        if isinstance(value, str):
            value = value.replace(",", ".")
        return value


class CreatePaymentResponse(BaseModel):
    payment_id: UUID
    amount: Decimal
    payment_method: PaymentMethodType
    payment_purpose: PaymentPurposeType
    appointment_id: UUID | None
    vip_client_id: UUID | None
    created_at: datetime
