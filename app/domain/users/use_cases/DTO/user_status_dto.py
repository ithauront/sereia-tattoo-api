from uuid import UUID
from pydantic import BaseModel


class ActivateUserInput(BaseModel):
    user_id: UUID


class DeactivateUserInput(BaseModel):
    user_id: UUID
    actor_id: UUID


class DemoteUserInput(BaseModel):
    user_id: UUID
    actor_id: UUID


class PromoteUserInput(BaseModel):
    user_id: UUID
