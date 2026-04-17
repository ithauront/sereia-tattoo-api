from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import exists, func, literal, select

from app.application.studio.repositories.payments_repository import PaymentsRepository

from sqlalchemy.orm import Session

from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.finances.entities.payment import Payment
from app.infrastructure.sqlalchemy.models.payment import PaymentModel


class SQLAlchemyPaymentsRepository(PaymentsRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, payment: Payment) -> None:
        orm_payment = PaymentModel(
            id=payment.id,
            amount=payment.amount,
            payment_method=payment.payment_method,
            vip_client_id=payment.vip_client_id,
            appointment_id=payment.appointment_id,
            external_reference=payment.external_reference,
            description=payment.description,
        )
        self.session.add(orm_payment)
        self.session.flush()

    def find_by_id(self, payment_id: UUID) -> Optional[Payment]:
        payment_in_question = select(PaymentModel).where(PaymentModel.id == payment_id)
        orm_payment = self.session.scalar(payment_in_question)

        if orm_payment is None:
            return None

        return self._to_entity(orm_payment)

    def find_many_by_vip_client_id(
        self,
        *,
        vip_client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[Payment]:
        payments_in_question = select(PaymentModel).where(
            PaymentModel.vip_client_id == vip_client_id
        )
        payments_in_question = self._apply_order(payments_in_question, direction)
        payments_in_question = payments_in_question.limit(limit).offset(offset)

        orm_payments = self.session.scalars(payments_in_question).all()

        return [self._to_entity(payment) for payment in orm_payments]

    def count_by_vip_client_id(self, vip_client_id: UUID) -> int:
        total = select(func.count(PaymentModel.id)).where(
            PaymentModel.vip_client_id == vip_client_id
        )

        return self.session.scalar(total) or 0

    def find_many_by_appointment_id(self, appointment_id: UUID) -> List[Payment]:
        payments_in_question = select(PaymentModel).where(
            PaymentModel.appointment_id == appointment_id
        )

        orm_payment = self.session.scalars(payments_in_question).all()

        return [self._to_entity(payment) for payment in orm_payment]

    def sum_by_vip_client_id(self, vip_client_id: UUID) -> Decimal:
        sum_of_payments = select(
            func.coalesce(func.sum(PaymentModel.amount), literal(Decimal("0")))
        ).where(PaymentModel.vip_client_id == vip_client_id)
        result = Decimal(self.session.scalar(sum_of_payments))
        return result

    def sum_by_appointment_id(self, appointment_id: UUID) -> Decimal:
        sum_of_payments = select(
            func.coalesce(func.sum(PaymentModel.amount), literal(Decimal("0")))
        ).where(PaymentModel.appointment_id == appointment_id)

        result = Decimal(self.session.scalar(sum_of_payments))
        return result

    def find_by_external_reference(self, external_reference: str) -> Optional[Payment]:
        payment_in_question = select(PaymentModel).where(
            PaymentModel.external_reference == external_reference
        )
        orm_payment = self.session.scalar(payment_in_question)

        if orm_payment is None:
            return None

        return self._to_entity(orm_payment)

    def exists_by_external_reference(self, external_reference: str) -> bool:
        payment = select(
            exists().where(PaymentModel.external_reference == external_reference)
        )

        return self.session.scalar(payment) or False

    def _to_entity(self, orm_payment: PaymentModel) -> Payment:

        return Payment(
            id=UUID(str(orm_payment.id)),
            amount=orm_payment.amount,
            payment_method=orm_payment.payment_method,
            vip_client_id=(
                UUID(str(orm_payment.vip_client_id))
                if orm_payment.vip_client_id is not None
                else None
            ),
            appointment_id=(
                UUID(str(orm_payment.appointment_id))
                if orm_payment.appointment_id is not None
                else None
            ),
            external_reference=orm_payment.external_reference,
            description=orm_payment.description,
            created_at=orm_payment.created_at,
        )

    def _apply_order(self, query, direction: Direction):
        if direction == Direction.asc:
            return query.order_by(
                PaymentModel.created_at.asc(),
                PaymentModel.id.asc(),
            )
        return query.order_by(
            PaymentModel.created_at.desc(),
            PaymentModel.id.desc(),
        )
