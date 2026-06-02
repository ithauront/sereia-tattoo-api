from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.application.studio.repositories.refunds_repository import RefundsRepository
from app.application.studio.use_cases.DTO.commun import Direction
from app.core.types.refund_filter_types import RefundFilters
from app.domain.studio.finances.entities.refund import Refund


class FakeRefundsRepository(RefundsRepository):
    def __init__(self):
        self._refunds: List[Refund] = []

    def create(self, refund: Refund) -> None:
        self._refunds.append(refund)

    def find_by_id(self, refund_id: UUID) -> Optional[Refund]:
        for refund in self._refunds:
            if refund.id == refund_id:
                return refund
        return None

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

        filtered_refunds = [
            refund
            for refund in self._refunds
            if all(condition(refund) for condition in conditions)
        ]

        ordered_refunds = self._order(filtered_refunds, direction=direction)

        return ordered_refunds[defensive_offset : defensive_offset + defensive_limit]

    def count(self, *, filters: RefundFilters) -> int:
        conditions = self._build_filters(filters=filters)

        total: int = 0

        for refund in self._refunds:
            if all(condition(refund) for condition in conditions):
                total += 1

        return total

    def sum_amount(self, *, filters: RefundFilters) -> Decimal:
        conditions = self._build_filters(filters=filters)

        total: Decimal = Decimal("0")

        for refund in self._refunds:
            if all(condition(refund) for condition in conditions):
                total += refund.amount

        return total

    def _build_filters(self, filters: RefundFilters) -> List:
        conditions = []

        if filters.appointment_id is not None:
            conditions.append(
                lambda refund: refund.appointment_id == filters.appointment_id
            )

        if filters.payment_id is not None:
            conditions.append(lambda refund: refund.payment_id == filters.payment_id)

        if filters.creator_id is not None:
            conditions.append(
                lambda refund: refund.created_by_user_id == filters.creator_id
            )

        if filters.refund_method is not None:
            conditions.append(
                lambda refund: refund.refund_method == filters.refund_method
            )

        if filters.refund_status is not None:
            conditions.append(
                lambda refund: refund.refund_status == filters.refund_status
            )

        if filters.created_at_from is not None:
            conditions.append(
                lambda refund: refund.created_at >= filters.created_at_from
            )

        if filters.created_at_to is not None:
            conditions.append(lambda refund: refund.created_at <= filters.created_at_to)

        return conditions

    def _order(self, refunds: List[Refund], direction: Direction = Direction.desc):
        reverse = direction == Direction.desc
        return sorted(
            refunds,
            key=lambda refund: (refund.created_at, refund.id),
            reverse=reverse,
        )
