from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.studio.users.entities.vip_client import VipClient


class VipClientsRepository(ABC):
    @abstractmethod
    def create(self, vip_client: VipClient) -> None: ...

    @abstractmethod
    def update(self, vip_client: VipClient) -> None: ...

    @abstractmethod
    def find_by_id(self, vip_client_id: UUID) -> Optional[VipClient]: ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[VipClient]: ...

    @abstractmethod
    def find_by_phone(self, phone: str) -> Optional[VipClient]: ...

    @abstractmethod
    def find_by_client_code(self, client_code: str) -> Optional[VipClient]: ...

    @abstractmethod
    def find_many(self) -> List[VipClient]: ...
