from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.studio.repositories.audit_logs_repository import (
    AuditLogsRepository,
)
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.infrastructure.sqlalchemy.models.audit_logs import AuditLogsModel


class SQLAlchemyAuditLogsRepository(AuditLogsRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, audit_log: AuditLogEntry) -> None:

        orm_audit_log = AuditLogsModel(
            entity_name=audit_log.entity_name,
            entity_id=audit_log.entity_id,
            action=audit_log.action,
            actor_id=audit_log.actor_id,
            actor_type=audit_log.actor_type,
            performed_at=audit_log.performed_at,
            changes=audit_log.changes,
            reason=audit_log.reason,
        )

        self.session.add(orm_audit_log)
        self.session.flush()

    def find_many_by_entity_name(
        self, *, entity_name: str, limit: int = 100, offset: int = 0
    ) -> List[AuditLogEntry]:
        logs_in_question = (
            select(AuditLogsModel)
            .where(AuditLogsModel.entity_name == entity_name)
            .order_by(AuditLogsModel.performed_at.desc())
        )
        logs_in_question = logs_in_question.limit(limit).offset(offset)

        orm_audit_logs = self.session.scalars(logs_in_question).all()

        return [self._to_dto_entry(audit_log) for audit_log in orm_audit_logs]

    def find_many_by_entity_id(self, entity_id: UUID) -> List[AuditLogEntry]:
        logs_in_question = (
            select(AuditLogsModel)
            .where(AuditLogsModel.entity_id == entity_id)
            .order_by(AuditLogsModel.performed_at.desc())
        )

        orm_audit_logs = self.session.scalars(logs_in_question).all()

        return [self._to_dto_entry(audit_log) for audit_log in orm_audit_logs]

    def find_many_by_actor(
        self, *, actor_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[AuditLogEntry]:
        logs_in_question = (
            select(AuditLogsModel)
            .where(AuditLogsModel.actor_id == actor_id)
            .order_by(AuditLogsModel.performed_at.desc())
        )
        logs_in_question = logs_in_question.limit(limit).offset(offset)

        orm_audit_logs = self.session.scalars(logs_in_question).all()

        return [self._to_dto_entry(audit_log) for audit_log in orm_audit_logs]

    def _to_dto_entry(self, audit_log: AuditLogsModel) -> AuditLogEntry:
        return AuditLogEntry(
            entity_name=audit_log.entity_name,
            entity_id=audit_log.entity_id,
            action=audit_log.action,
            actor_id=audit_log.actor_id,
            actor_type=audit_log.actor_type,
            performed_at=audit_log.performed_at,
            changes=audit_log.changes,
            reason=audit_log.reason,
        )
