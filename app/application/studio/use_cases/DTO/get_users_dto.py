from typing import List
from uuid import UUID
from pydantic import BaseModel, Field


from enum import Enum

from app.application.studio.use_cases.DTO.commun import Direction
from app.application.studio.use_cases.DTO.user_output_dto import UserOutput
from app.application.studio.use_cases.DTO.vip_client_output import VipClientOutput


class UsersOrderBy(str, Enum):
    username = "username"
    created_at = "created_at"


class VipClientsOrderBy(str, Enum):
    first_name = "first_name"
    last_name = "last_name"
    created_at = "created_at"
    updated_at = "updated_at"


class ListUsersInput(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)
    order_by: UsersOrderBy = UsersOrderBy.username
    direction: Direction = Direction.asc


class ListVipClientsInput(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1)
    order_by: VipClientsOrderBy = VipClientsOrderBy.first_name
    direction: Direction = Direction.asc


class ListVipClientsOutput(BaseModel):
    vip_clients: List[VipClientOutput]


class ListUsersOutput(BaseModel):
    users: List[UserOutput]


class GetUserInput(BaseModel):
    user_id: UUID


class GetVipClientInput(BaseModel):
    vip_client_id: UUID
