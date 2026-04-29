from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.application.studio.use_cases.DTO.list_client_credit_entries import Direction
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry
from app.core.types.client_credit_source_type import (
    ClientCreditSourceType,
)


class ClientCreditEntriesRepository(ABC):
    @abstractmethod
    def create(self, client_credit_entry: ClientCreditEntry) -> None: ...

    @abstractmethod
    def get_balance(self, *, vip_client_id: UUID) -> int: ...

    @abstractmethod
    def find_by_id(self, credit_id: UUID) -> Optional[ClientCreditEntry]: ...

    @abstractmethod
    def find_many_by_vip_client_id(
        self,
        *,
        vip_client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[ClientCreditEntry]: ...

    @abstractmethod
    def count_by_vip_client_id(self, *, vip_client_id: UUID) -> int: ...

    @abstractmethod
    def find_many_by_source_id(
        self,
        *,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[ClientCreditEntry]: ...

    @abstractmethod
    def count_by_source_id(self, *, source_id: UUID) -> int: ...

    @abstractmethod
    def find_many_by_source_type_and_vip_client_id(
        self,
        *,
        source_type: ClientCreditSourceType,
        vip_client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[ClientCreditEntry]: ...

    @abstractmethod
    def count_by_source_type_and_vip_client_id(
        self, *, source_type: ClientCreditSourceType, vip_client_id: UUID
    ) -> int: ...
