from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry


# TODO: quando tudo estiver pronto adicionar o audit log a algum metodo apenas para testar se funciona
class AuditLogsRepository(ABC):
    @abstractmethod
    def create(self, audit_log: AuditLogEntry) -> None: ...

    @abstractmethod
    def find_many_by_entity_name(
        self,
        *,
        entity_name: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]: ...

    @abstractmethod
    def find_many_by_entity_id(
        self,
        entity_id: UUID,
    ) -> List[AuditLogEntry]: ...

    @abstractmethod
    def find_many_by_actor(
        self,
        *,
        actor_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]: ...
