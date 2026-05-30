from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.application.studio.use_cases.DTO.commun import Direction
from app.core.types.refund_filter_types import RefundFilters
from app.domain.studio.finances.entities.refund import Refund


class RefundsRepository(ABC):
    @abstractmethod
    def create(self, refund: Refund) -> None: ...

    @abstractmethod
    def find_by_id(self, refund_id: UUID) -> Optional[Refund]: ...

    @abstractmethod
    def find_many(
        self,
        *,
        filters: RefundFilters,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[Refund]: ...

    @abstractmethod
    def count(
        self,
        *,
        filters: RefundFilters,
    ) -> int: ...

    @abstractmethod
    def sum_amount(
        self,
        *,
        filters: RefundFilters,
    ) -> Decimal: ...
