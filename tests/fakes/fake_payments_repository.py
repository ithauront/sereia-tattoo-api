from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.application.studio.repositories.payments_repository import PaymentsRepository
from app.application.studio.use_cases.DTO.commun import Direction
from app.core.exceptions.payment import DuplicateExternalReferenceError
from app.domain.studio.finances.entities.payment import Payment


class FakePaymentsRepository(PaymentsRepository):
    def __init__(self):
        self._payments: List[Payment] = []

    def create(self, payment: Payment) -> None:
        if (
            payment.external_reference is not None
            and self.exists_by_external_reference(payment.external_reference)
        ):
            raise DuplicateExternalReferenceError()
        # This simulates the constraint unique=True of the model for payment in sqlAlchemy layer
        self._payments.append(payment)

    def find_by_id(self, payment_id: UUID) -> Optional[Payment]:
        for payment in self._payments:
            if payment.id == payment_id:
                return payment
        return None

    def find_many_by_vip_client_id(
        self, *, vip_client_id: UUID, limit=100, offset=0, direction=Direction.desc
    ) -> List[Payment]:
        payments = [
            payment
            for payment in self._payments
            if payment.vip_client_id == vip_client_id
        ]
        return self._order(payments, direction)[offset : offset + limit]

    def count_by_vip_client_id(self, vip_client_id: UUID) -> int:
        return len(
            [
                payment
                for payment in self._payments
                if payment.vip_client_id == vip_client_id
            ]
        )

    def find_many_by_appointment_id(self, appointment_id: UUID) -> List[Payment]:
        payments = [
            payment
            for payment in self._payments
            if payment.appointment_id == appointment_id
        ]

        return payments

    def sum_by_vip_client_id(self, vip_client_id: UUID) -> Decimal:
        total: Decimal = Decimal("0")
        for payment in self._payments:
            if payment.vip_client_id == vip_client_id:
                total += payment.amount
        return total

    def sum_by_appointment_id(self, appointment_id: UUID) -> Decimal:
        total: Decimal = Decimal("0")
        for payment in self._payments:
            if payment.appointment_id == appointment_id:
                total += payment.amount
        return total

    def find_by_external_reference(self, external_reference: str) -> Optional[Payment]:
        for payment in self._payments:
            if payment.external_reference == external_reference:
                return payment
        return None

    def exists_by_external_reference(self, external_reference: str) -> bool:
        for payment in self._payments:
            if payment.external_reference == external_reference:
                return True
        return False

    def _order(self, payments, direction: Direction = Direction.desc):
        reverse = direction == Direction.desc
        return sorted(
            payments,
            key=lambda payment: (payment.created_at, payment.id),
            reverse=reverse,
        )
