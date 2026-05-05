from typing import List
from uuid import UUID

from app.application.studio.repositories.audit_logs_repository import (
    AuditLogsRepository,
)
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry


class FakeAuditLogsRepository(AuditLogsRepository):
    def __init__(self):
        self._logs: list[AuditLogEntry] = []

    def create(self, audit_log: AuditLogEntry) -> None:
        self._logs.append(audit_log)

    def find_many_by_entity_name(
        self, *, entity_name: str, limit: int = 100, offset: int = 0
    ) -> List[AuditLogEntry]:
        logs = [log for log in self._logs if log.entity_name == entity_name]
        logs.sort(key=lambda log: log.performed_at, reverse=True)

        return logs[offset : offset + limit]

    def find_many_by_actor(
        self, *, actor_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[AuditLogEntry]:
        logs = [log for log in self._logs if log.actor_id == actor_id]
        logs.sort(key=lambda log: log.performed_at, reverse=True)

        return logs[offset : offset + limit]

    def find_many_by_entity_id(self, entity_id: UUID) -> List[AuditLogEntry]:
        logs = [log for log in self._logs if log.entity_id == entity_id]
        logs.sort(key=lambda log: log.performed_at, reverse=True)

        return logs
