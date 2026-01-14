from uuid import UUID
from pydantic import BaseModel


class FirstActivationInput(BaseModel):
    user_id: UUID
    token_version: int
    username: str
    password: str
