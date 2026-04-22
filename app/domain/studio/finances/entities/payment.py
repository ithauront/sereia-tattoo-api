from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.exceptions.payment import (
    PaymentMustBeGreaterThanZeroError,
    VipClientIdIsRequiredError,
)
from app.domain.studio.finances.enums.payment_enums import PaymentMethodType


# TODO: fazer o model o repo, o fake repo e o teste do fake repo
class Payment:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        amount: Decimal,
        payment_method: PaymentMethodType,
        vip_client_id: UUID | None = None,
        appointment_id: UUID | None = None,
        external_reference: str | None = None,
        # external reference for if we accept automatic payment one day
        description: str | None = None,
        created_at: datetime | None = None,
    ):

        now = datetime.now(timezone.utc)

        if amount <= 0:
            raise PaymentMustBeGreaterThanZeroError()

        if payment_method == PaymentMethodType.CLIENT_CREDIT and not vip_client_id:
            raise VipClientIdIsRequiredError()

        self.id = id or uuid4()
        self.amount = amount
        self.payment_method = payment_method
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
        vip_client_id: UUID | None = None,
        appointment_id: UUID | None = None,
        external_reference: str | None = None,
        description: str | None = None,
    ) -> "Payment":
        return cls(
            amount=amount,
            payment_method=payment_method,
            vip_client_id=vip_client_id,
            appointment_id=appointment_id,
            external_reference=external_reference,
            description=description,
            created_at=None,
        )
