from typing import List, Optional
from uuid import UUID

from app.domain.users.entities.vip_client import VipClient
from app.domain.users.repositories.vip_clients_repository import VipClientsRepository


class FakeVipClientsRepository(VipClientsRepository):
    def __init__(self):
        self.vip_clients: List[VipClient] = []

    def create(self, vip_client: VipClient) -> None:
        self.vip_clients.append(vip_client)

    def update(self, vip_client: VipClient) -> None:
        for index, user_in_question in enumerate(self.vip_clients):
            if user_in_question.id == vip_client.id:
                self.vip_clients[index] = vip_client
                return

    def find_by_email(self, email: str) -> Optional[VipClient]:
        for user in self.vip_clients:
            if user.email == email:
                return user
        return None

    def find_by_id(self, vip_client_id: UUID) -> Optional[VipClient]:
        for user in self.vip_clients:
            if user.id == vip_client_id:
                return user
        return None

    def find_by_phone(self, phone: str) -> Optional[VipClient]:
        for user in self.vip_clients:
            if user.phone == phone:
                return user
        return None

    def find_by_client_code(self, client_code: str) -> Optional[VipClient]:
        for user in self.vip_clients:
            if user.client_code.value == client_code:
                return user
        return None

    def find_many(self) -> List[VipClient]:
        return list(self.vip_clients)
