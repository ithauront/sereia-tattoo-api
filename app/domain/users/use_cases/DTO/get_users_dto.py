from typing import List
from uuid import UUID
from pydantic import BaseModel, Field


from enum import Enum

from app.domain.users.use_cases.DTO.user_output_dto import UserOutput


class OrderBy(str, Enum):
    username = "username"
    created_at = "created_at"


class Direction(str, Enum):
    asc = "asc"
    desc = "desc"


class ListUsersInput(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)
    order_by: OrderBy = OrderBy.username
    direction: Direction = Direction.asc


class ListUsersOutput(BaseModel):
    users: List[UserOutput]


class GetUserInput(BaseModel):
    user_id: UUID
