from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOutput(BaseModel):
    id: UUID
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserVerifyDTO(BaseModel):
    id: UUID
    is_active: bool
    is_admin: bool
