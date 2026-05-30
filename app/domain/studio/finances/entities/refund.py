from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.exceptions.refund import (
    RefundMustBeGreaterThanZeroError,
    RefundsWithoutAppointmentRequireReasonError,
    VipClientIdIsRequiredForCreditRefundError,
)
from app.core.types.refund_enums import RefundMethodType, RefundStatus
from app.domain.utils.ensure_enum import ensure_enum

"""
Refund amounts are always stored as positive values.
Net paid amounts should be calculated as:
net_paid = total_payments - total_refunds
"""


# TODO talvez fazer letodos aqui para mudança de status, mark as completed, mark as pending etc.
# TODO: no use_case de criar o refund temos que verificar o total da payment reference id e verificar se ja ha refunds desse payment o total de refunds não pode ter valor maior do que o total payment.
# TODO: fazer repo e fazer model e implementar repo no sqlalchemy add o repo ao uow depois espelhar nos testes o repo e a adição ao uow e o teste do repo fake
class Refund:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        amount: Decimal,
        refund_status: RefundStatus = RefundStatus.COMPLETED,
        refund_method: RefundMethodType = RefundMethodType.CLIENT_CREDIT,
        vip_client_id: UUID | None = None,
        appointment_id: UUID | None,
        payment_id: UUID,
        reason: str | None = None,
        created_by_user_id: UUID,
        created_at: datetime | None = None,
    ):

        now = datetime.now(timezone.utc)

        if amount <= 0:
            raise RefundMustBeGreaterThanZeroError()

        if refund_method == RefundMethodType.CLIENT_CREDIT and not vip_client_id:
            raise VipClientIdIsRequiredForCreditRefundError()

        if not appointment_id and not (reason and reason.strip()):
            raise RefundsWithoutAppointmentRequireReasonError()

        self.id = id or uuid4()
        self.amount = amount
        self.refund_status = ensure_enum(refund_status, RefundStatus)
        self.refund_method = ensure_enum(refund_method, RefundMethodType)
        self.vip_client_id = vip_client_id
        self.appointment_id = appointment_id
        self.payment_id = payment_id
        self.reason = reason
        self.created_by_user_id = created_by_user_id
        self.created_at = created_at or now

    @property
    def is_client_credit_refund(self) -> bool:
        return self.refund_method == RefundMethodType.CLIENT_CREDIT

    @property
    def has_appointment_reference(self) -> bool:
        return self.appointment_id is not None

    @classmethod
    def create(
        cls,
        *,
        amount: Decimal,
        refund_status: RefundStatus = RefundStatus.COMPLETED,
        refund_method: RefundMethodType = RefundMethodType.CLIENT_CREDIT,
        vip_client_id: UUID | None = None,
        appointment_id: UUID | None = None,
        payment_id: UUID,
        reason: str | None = None,
        created_by_user_id: UUID,
    ) -> "Refund":
        return cls(
            amount=amount,
            refund_status=refund_status,
            refund_method=refund_method,
            vip_client_id=vip_client_id,
            appointment_id=appointment_id,
            payment_id=payment_id,
            reason=reason,
            created_by_user_id=created_by_user_id,
            created_at=None,
        )
