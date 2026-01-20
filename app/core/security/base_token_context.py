from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class BaseTokenContext:
    user_id: UUID
    token_version: int
