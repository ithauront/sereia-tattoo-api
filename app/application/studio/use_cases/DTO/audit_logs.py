from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.core.types.audit_actor_type import AuditActorType


@dataclass
class AuditLogEntry:
    entity_name: str
    entity_id: UUID
    action: str
    actor_id: UUID | None
    actor_type: AuditActorType
    performed_at: datetime
    changes: dict | None = None
    reason: str | None = None


# Changes will be a dict logging what changes with from and to. eg:
# changes={ "phone": { "from": old_phone, "to": new_phone, } }
