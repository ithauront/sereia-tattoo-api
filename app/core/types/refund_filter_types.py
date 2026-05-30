from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.types.refund_enums import RefundMethodType, RefundStatus


@dataclass(frozen=True)
class RefundFilters:
    appointment_id: Optional[UUID] = None
    payment_id: Optional[UUID] = None
    creator_id: Optional[UUID] = None
    refund_method: Optional[RefundMethodType] = None
    refund_status: Optional[RefundStatus] = None

    created_at_from: Optional[datetime] = None
    created_at_to: Optional[datetime] = None

    # factories

    @staticmethod
    def by_appointment(appointment_id: UUID) -> "RefundFilters":
        return RefundFilters(appointment_id=appointment_id)

    @staticmethod
    def by_payment(payment_id: UUID) -> "RefundFilters":
        return RefundFilters(payment_id=payment_id)

    @staticmethod
    def by_creator(creator_id: UUID) -> "RefundFilters":
        return RefundFilters(creator_id=creator_id)

    @staticmethod
    def by_refund_method(refund_method: RefundMethodType) -> "RefundFilters":
        return RefundFilters(refund_method=refund_method)
