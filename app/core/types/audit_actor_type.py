from enum import Enum


class AuditActorType(str, Enum):
    USER = "user"
    SYSTEM = "system"
