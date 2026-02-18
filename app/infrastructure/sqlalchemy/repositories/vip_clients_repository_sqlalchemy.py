from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from app.domain.users.entities.value_objects.client_code import ClientCode
from app.domain.users.entities.vip_client import VipClient
from app.domain.users.repositories.vip_clients_repository import VipClientsRepository
from sqlalchemy.orm import Session

from app.infrastructure.sqlalchemy.models.vip_client import VipClientModel


class SQLAlchemyVipClientsRepository(VipClientsRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, vip_client: VipClient) -> None:
        orm_vip_client = VipClientModel(
            id=vip_client.id,
            first_name=vip_client.first_name,
            last_name=vip_client.last_name,
            email=vip_client.email,
            phone=vip_client.phone,
            client_code=vip_client.client_code.value,
        )
        self.session.add(orm_vip_client)
        self.session.flush()

    def update(self, vip_client: VipClient) -> None:
        vip_client_in_question = select(VipClientModel).where(
            VipClientModel.id == vip_client.id
        )
        orm_vip_client = self.session.scalar(vip_client_in_question)
        if orm_vip_client is None:
            return

        orm_vip_client.first_name = vip_client.first_name
        orm_vip_client.last_name = vip_client.last_name
        orm_vip_client.email = vip_client.email
        orm_vip_client.phone = vip_client.phone
        orm_vip_client.client_code = str(vip_client.client_code)

        self.session.flush()

    def find_by_id(self, vip_client_id: UUID) -> Optional[VipClient]:
        vip_client_in_question = select(VipClientModel).where(
            VipClientModel.id == vip_client_id
        )
        orm_vip_client = self.session.scalar(vip_client_in_question)

        return self._to_entity(orm_vip_client)

    def find_by_email(self, email: str) -> Optional[VipClient]:
        vip_client_in_question = select(VipClientModel).where(
            VipClientModel.email == email
        )
        orm_vip_client = self.session.scalar(vip_client_in_question)

        return self._to_entity(orm_vip_client)

    def find_by_phone(self, phone: str) -> Optional[VipClient]:
        vip_client_in_question = select(VipClientModel).where(
            VipClientModel.phone == phone
        )
        orm_vip_client = self.session.scalar(vip_client_in_question)

        return self._to_entity(orm_vip_client)

    def find_by_client_code(self, client_code: str) -> Optional[VipClient]:
        vip_client_in_question = select(VipClientModel).where(
            VipClientModel.client_code == client_code
        )
        orm_vip_client = self.session.scalar(vip_client_in_question)

        return self._to_entity(orm_vip_client)

    def find_many(self) -> List[VipClient]:
        vip_clients_in_question = select(VipClientModel)
        orm_vip_clients = self.session.scalars(vip_clients_in_question).all()
        entities = []
        for orm_vip_client in orm_vip_clients:
            entity = self._to_entity(orm_vip_client)
            if entity is not None:
                entities.append(entity)

        return entities

    def _to_entity(
        self, orm_vip_client: Optional[VipClientModel]
    ) -> Optional[VipClient]:
        if orm_vip_client is None:
            return None

        return VipClient(
            id=UUID(str(orm_vip_client.id)),
            first_name=orm_vip_client.first_name,
            last_name=orm_vip_client.last_name,
            email=orm_vip_client.email,
            phone=orm_vip_client.phone,
            client_code=ClientCode(orm_vip_client.client_code),
            created_at=orm_vip_client.created_at,
            updated_at=orm_vip_client.updated_at,
        )
