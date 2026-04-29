from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func

from app.application.studio.repositories.client_credit_entries_repository import (
    ClientCreditEntriesRepository,
)
from sqlalchemy.orm import Session

from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry
from app.core.types.client_credit_source_type import (
    ClientCreditSourceType,
)
from app.infrastructure.sqlalchemy.models.client_credit_entry import (
    ClientCreditEntryModel,
)


class SQLAlchemyClientCreditEntriesRepository(ClientCreditEntriesRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, client_credit_entry: ClientCreditEntry) -> None:
        orm_client_credit_entry = ClientCreditEntryModel(
            id=client_credit_entry.id,
            vip_client_id=client_credit_entry.vip_client_id,
            source_id=client_credit_entry.source_id,
            source_type=client_credit_entry.source_type,
            related_entry_id=client_credit_entry.related_entry_id,
            quantity=client_credit_entry.quantity,
            reason=client_credit_entry.reason,
            created_at=client_credit_entry.created_at,
        )
        self.session.add(orm_client_credit_entry)
        self.session.flush()

    def get_balance(self, *, vip_client_id: UUID) -> int:
        credits_to_sum = select(
            func.coalesce(func.sum(ClientCreditEntryModel.quantity), 0)
        ).where(ClientCreditEntryModel.vip_client_id == vip_client_id)

        balance = self.session.scalar(credits_to_sum)

        return balance or 0

    def find_by_id(self, credit_id: UUID) -> Optional[ClientCreditEntry]:
        credit_in_question = select(ClientCreditEntryModel).where(
            ClientCreditEntryModel.id == credit_id
        )
        orm_client_credit_entry = self.session.scalar(credit_in_question)

        if orm_client_credit_entry is None:
            return None

        return self._to_entity(orm_client_credit_entry)

    def find_many_by_vip_client_id(
        self,
        *,
        vip_client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[ClientCreditEntry]:
        credits_in_question = select(ClientCreditEntryModel).where(
            ClientCreditEntryModel.vip_client_id == vip_client_id
        )
        credits_in_question = self._apply_order(credits_in_question, direction)

        credits_in_question = credits_in_question.limit(limit).offset(offset)

        orm_client_credit_entries = self.session.scalars(credits_in_question).all()

        return [self._to_entity(entry) for entry in orm_client_credit_entries]

    def count_by_vip_client_id(self, *, vip_client_id: UUID):
        total = select(func.count(ClientCreditEntryModel.id)).where(
            ClientCreditEntryModel.vip_client_id == vip_client_id
        )

        return self.session.scalar(total) or 0

    def find_many_by_source_id(
        self,
        *,
        source_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[ClientCreditEntry]:
        credits_in_question = select(ClientCreditEntryModel).where(
            ClientCreditEntryModel.source_id == source_id
        )
        credits_in_question = self._apply_order(credits_in_question, direction)

        credits_in_question = credits_in_question.limit(limit).offset(offset)

        orm_client_credit_entries = self.session.scalars(credits_in_question).all()

        return [self._to_entity(entry) for entry in orm_client_credit_entries]

    def count_by_source_id(self, *, source_id: UUID):
        total = select(func.count(ClientCreditEntryModel.id)).where(
            ClientCreditEntryModel.source_id == source_id
        )

        return self.session.scalar(total) or 0

    def find_many_by_source_type_and_vip_client_id(
        self,
        *,
        source_type: ClientCreditSourceType,
        vip_client_id: UUID,
        limit: int = 100,
        offset: int = 0,
        direction: Direction = Direction.desc,
    ) -> List[ClientCreditEntry]:
        credits_in_question = select(ClientCreditEntryModel).where(
            ClientCreditEntryModel.vip_client_id == vip_client_id,
            ClientCreditEntryModel.source_type == source_type,
        )
        credits_in_question = self._apply_order(credits_in_question, direction)

        credits_in_question = credits_in_question.limit(limit).offset(offset)

        orm_client_credit_entries = self.session.scalars(credits_in_question).all()

        return [self._to_entity(entry) for entry in orm_client_credit_entries]

    def count_by_source_type_and_vip_client_id(
        self, *, source_type: ClientCreditSourceType, vip_client_id: UUID
    ):
        total = select(func.count(ClientCreditEntryModel.id)).where(
            ClientCreditEntryModel.vip_client_id == vip_client_id,
            ClientCreditEntryModel.source_type == source_type,
        )

        return self.session.scalar(total) or 0

    def _to_entity(
        self, orm_client_credit_entry: ClientCreditEntryModel
    ) -> ClientCreditEntry:

        return ClientCreditEntry(
            id=UUID(str(orm_client_credit_entry.id)),
            vip_client_id=UUID(str(orm_client_credit_entry.vip_client_id)),
            source_id=UUID(str(orm_client_credit_entry.source_id)),
            source_type=orm_client_credit_entry.source_type,
            related_entry_id=(
                UUID(str(orm_client_credit_entry.related_entry_id))
                if orm_client_credit_entry.related_entry_id
                else None
            ),
            quantity=orm_client_credit_entry.quantity,
            reason=orm_client_credit_entry.reason,
            created_at=orm_client_credit_entry.created_at,
        )

    def _apply_order(self, query, direction: Direction):
        if direction == Direction.asc:
            return query.order_by(
                ClientCreditEntryModel.created_at.asc(),
                ClientCreditEntryModel.id.asc(),
            )
        return query.order_by(
            ClientCreditEntryModel.created_at.desc(),
            ClientCreditEntryModel.id.desc(),
        )
