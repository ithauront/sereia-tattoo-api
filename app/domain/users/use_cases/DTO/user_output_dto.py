from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserOutput(BaseModel):
    id: UUID
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
