from typing import List, Optional
from uuid import UUID

from app.application.studio.repositories.client_credit_entries_repository import (
    ClientCreditEntriesRepository,
)
from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry
from app.core.types.client_credit_source_type import (
    ClientCreditSourceType,
)


class FakeClientCreditEntriesRepository(ClientCreditEntriesRepository):
    def __init__(self):
        self._entries: list[ClientCreditEntry] = []

    def create(self, client_credit_entry: ClientCreditEntry) -> None:
        self._entries.append(client_credit_entry)

    def get_balance(self, *, vip_client_id: UUID) -> int:
        balance = 0
        for credit in self._entries:
            if credit.vip_client_id == vip_client_id:
                balance = balance + credit.quantity
        return balance

    def find_by_id(self, credit_id: UUID) -> Optional[ClientCreditEntry]:
        for entry in self._entries:
            if entry.id == credit_id:
                return entry
        return None

    def find_many_by_vip_client_id(
        self,
        *,
        vip_client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> list[ClientCreditEntry]:
        entries = [
            entry for entry in self._entries if entry.vip_client_id == vip_client_id
        ]

        return self._order(entries, direction)[offset : offset + limit]

    def count_by_vip_client_id(self, *, vip_client_id: UUID):
        return len(
            [entry for entry in self._entries if entry.vip_client_id == vip_client_id]
        )

    def find_many_by_source_id(
        self,
        *,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[ClientCreditEntry]:
        entries = [entry for entry in self._entries if entry.source_id == source_id]

        return self._order(entries, direction)[offset : offset + limit]

    def count_by_source_id(self, *, source_id: UUID):
        return len([entry for entry in self._entries if entry.source_id == source_id])

    def find_many_by_source_type_and_vip_client_id(
        self,
        *,
        source_type: ClientCreditSourceType,
        vip_client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[ClientCreditEntry]:
        entries = [
            entry
            for entry in self._entries
            if entry.source_type == source_type and entry.vip_client_id == vip_client_id
        ]

        return self._order(entries, direction)[offset : offset + limit]

    def count_by_source_type_and_vip_client_id(
        self, *, source_type: ClientCreditSourceType, vip_client_id: UUID
    ):
        return len(
            [
                entry
                for entry in self._entries
                if entry.source_type == source_type
                and entry.vip_client_id == vip_client_id
            ]
        )

    def _order(self, entries, direction: Direction = Direction.desc):
        reverse = direction == Direction.desc
        return sorted(
            entries,
            key=lambda entry: (entry.created_at, entry.id),
            reverse=reverse,
        )
