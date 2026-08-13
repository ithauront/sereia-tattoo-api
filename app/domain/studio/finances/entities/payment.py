from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.exceptions.payment import (
    PaymentLinkToAppointmentIsCorruptedError,
    PaymentMustBeGreaterThanZeroError,
    PaymentMustHaveDepositPurposeError,
    PaymentWithoutAppointmentRequireDescriptionError,
    VipClientIdIsRequiredError,
)
from app.core.types.payment_enums import PaymentMethodType, PaymentPurposeType
from app.domain.studio.finances.events.deposit_payment_recorded_event import (
    DepositPaymentRecordedEvent,
)
from app.domain.utils.ensure_enum import ensure_enum


class Payment:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        amount: Decimal,
        payment_method: PaymentMethodType,
        payment_purpose: PaymentPurposeType,
        vip_client_id: UUID | None = None,
        appointment_id: UUID | None = None,
        external_reference: str | None = None,
        # external reference for if we accept automatic payment one day
        description: str | None = None,
        created_at: datetime | None = None,
    ):

        now = datetime.now(timezone.utc)

        payment_method = ensure_enum(payment_method, PaymentMethodType)
        payment_purpose = ensure_enum(payment_purpose, PaymentPurposeType)

        if payment_method == PaymentMethodType.CLIENT_CREDIT and not vip_client_id:
            raise VipClientIdIsRequiredError()

        if amount <= 0:
            raise PaymentMustBeGreaterThanZeroError()

        if not appointment_id and not (description and description.strip()):
            raise PaymentWithoutAppointmentRequireDescriptionError()

        self.id = id or uuid4()
        self.amount = amount
        self.payment_method = payment_method
        self.payment_purpose = payment_purpose
        self.vip_client_id = vip_client_id
        self.appointment_id = appointment_id
        self.external_reference = external_reference
        self.description = description
        self.created_at = created_at or now

    @property
    def is_credit_payment(self) -> bool:
        return self.payment_method == PaymentMethodType.CLIENT_CREDIT

    @property
    def has_appointment(self) -> bool:
        return self.appointment_id is not None

    @classmethod
    def create(
        cls,
        *,
        amount: Decimal,
        payment_method: PaymentMethodType,
        payment_purpose: PaymentPurposeType,
        vip_client_id: UUID | None = None,
        appointment_id: UUID | None = None,
        external_reference: str | None = None,
        description: str | None = None,
    ) -> "Payment":
        return cls(
            amount=amount,
            payment_method=payment_method,
            payment_purpose=payment_purpose,
            vip_client_id=vip_client_id,
            appointment_id=appointment_id,
            external_reference=external_reference,
            description=description,
            created_at=None,
        )

    def record_deposit_event(self) -> DepositPaymentRecordedEvent:
        if self.appointment_id is None:
            raise PaymentLinkToAppointmentIsCorruptedError()
        if self.payment_purpose != PaymentPurposeType.DEPOSIT:
            raise PaymentMustHaveDepositPurposeError()
        return DepositPaymentRecordedEvent(amount=self.amount, appointment_id=self.appointment_id)
