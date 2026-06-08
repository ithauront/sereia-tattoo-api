from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.application.studio.repositories.refunds_repository import RefundsRepository
from app.application.studio.use_cases.DTO.commun import Direction
from app.core.types.refund_filter_types import RefundFilters
from app.domain.studio.finances.entities.refund import Refund
from app.infrastructure.sqlalchemy.models.refund import RefundModel
from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session


class SQLAlchemyRefundsRepository(RefundsRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, refund: Refund) -> None:
        orm_refund = RefundModel(
            id=refund.id,
            amount=refund.amount,
            refund_status=refund.refund_status,
            refund_method=refund.refund_method,
            vip_client_id=refund.vip_client_id,
            appointment_id=refund.appointment_id,
            payment_id=refund.payment_id,
            reason=refund.reason,
            created_by_user_id=refund.created_by_user_id,
            created_at=refund.created_at,
        )
        self.session.add(orm_refund)
        self.session.flush()

    def find_by_id(self, refund_id: UUID) -> Optional[Refund]:
        refund_in_question = select(RefundModel).where(RefundModel.id == refund_id)
        orm_refund = self.session.scalar(refund_in_question)

        if orm_refund is None:
            return None

        return self._to_entity(orm_refund)

    def find_many(
        self,
        *,
        filters: RefundFilters,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[Refund]:
        defensive_limit = max(0, limit)
        defensive_offset = max(0, offset)

        conditions = self._build_filters(filters=filters)
        refunds_in_question = select(RefundModel).where(*conditions)
        refunds_in_question = self._apply_order(refunds_in_question, direction=direction)
        refunds_in_question = refunds_in_question.limit(defensive_limit).offset(defensive_offset)

        return [self._to_entity(orm_refund) for orm_refund in self.session.scalars(refunds_in_question)]

    def count(self, *, filters: RefundFilters) -> int:
        conditions = self._build_filters(filters=filters)
        total = select(func.count(RefundModel.id)).where(*conditions)

        return self.session.scalar(total) or 0

    def sum_amount(self, *, filters: RefundFilters) -> Decimal:
        conditions = self._build_filters(filters=filters)
        sum_of_refunds = select(
            func.coalesce(func.sum(RefundModel.amount), literal(Decimal("0")))
        ).where(*conditions)

        return self.session.scalar(sum_of_refunds) or Decimal("0")

    def _build_filters(self, *, filters: RefundFilters) -> list:
        conditions = []

        if filters.appointment_id is not None:
            conditions.append(RefundModel.appointment_id == filters.appointment_id)

        if filters.payment_id is not None:
            conditions.append(RefundModel.payment_id == filters.payment_id)

        if filters.creator_id is not None:
            conditions.append(RefundModel.created_by_user_id == filters.creator_id)

        if filters.refund_method is not None:
            conditions.append(RefundModel.refund_method == filters.refund_method)

        if filters.refund_status is not None:
            conditions.append(RefundModel.refund_status == filters.refund_status)

        if filters.created_at_from is not None:
            conditions.append(RefundModel.created_at >= filters.created_at_from)

        if filters.created_at_to is not None:
            conditions.append(RefundModel.created_at <= filters.created_at_to)

        return conditions

    def _to_entity(self, orm_refund: RefundModel) -> Refund:
        return Refund(
            id=UUID(str(orm_refund.id)),
            amount=orm_refund.amount,
            refund_method=orm_refund.refund_method,
            refund_status=orm_refund.refund_status,
            appointment_id=(
                UUID(str(orm_refund.appointment_id)) if orm_refund.appointment_id is not None else None
            ),
            vip_client_id=(
                UUID(str(orm_refund.vip_client_id)) if orm_refund.vip_client_id is not None else None
            ),
            payment_id=UUID(str(orm_refund.payment_id)),
            reason=orm_refund.reason,
            created_by_user_id=UUID(str(orm_refund.created_by_user_id)),
            created_at=orm_refund.created_at,
        )

    def _apply_order(self, query, direction: Direction):
        if direction == Direction.asc:
            return query.order_by(
                RefundModel.created_at.asc(),
                RefundModel.id.asc(),
            )
        return query.order_by(
            RefundModel.created_at.desc(),
            RefundModel.id.desc(),
        )
