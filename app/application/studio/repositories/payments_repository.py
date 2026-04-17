from abc import ABC, abstractmethod

from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.finances.entities.payment import Payment


class PaymentsRepository(ABC):
    @abstractmethod
    def create(self, payment: Payment) -> None: ...

    @abstractmethod
    def find_by_id(self, payment_id: UUID) -> Optional[Payment]: ...

    @abstractmethod
    def find_many_by_vip_client_id(
        self,
        *,
        vip_client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[Payment]: ...

    @abstractmethod
    def count_by_vip_client_id(self, vip_client_id: UUID) -> int: ...

    @abstractmethod
    def find_many_by_appointment_id(self, appointment_id: UUID) -> List[Payment]: ...

    """ WARNING:
     These sum methods does NOT represent the real net balance.
     It only aggregates payments and does NOT consider refunds.
     Net balance must be calculated at the application/service layer
     by combining payments and refunds.
     """

    @abstractmethod
    def sum_by_vip_client_id(self, vip_client_id: UUID) -> Decimal: ...

    @abstractmethod
    def sum_by_appointment_id(self, appointment_id: UUID) -> Decimal: ...

    @abstractmethod
    def find_by_external_reference(
        self, external_reference: str
    ) -> Optional[Payment]: ...

    @abstractmethod
    def exists_by_external_reference(self, external_reference: str) -> bool: ...
