from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.types.payment_enums import PaymentMethodType, PaymentPurposeType
from app.domain.studio.users.entities.user import User


@dataclass(frozen=True)
class CreatePaymentInput:
    idempotency_key: UUID
    actor: User
    amount: Decimal
    payment_method: PaymentMethodType
    payment_purpose: PaymentPurposeType
    appointment_id: UUID | None = None
    credit_owner_vip_client_id: UUID | None = None
    description: str | None = None
    external_reference: str | None = None


@dataclass(frozen=True)
class CreatePaymentOutput:
    payment_id: UUID
    amount: Decimal
    payment_method: PaymentMethodType
    payment_purpose: PaymentPurposeType
    appointment_id: UUID | None
    vip_client_id: UUID | None
    created_at: datetime
