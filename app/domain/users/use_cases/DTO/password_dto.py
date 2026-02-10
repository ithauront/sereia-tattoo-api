from uuid import UUID
from pydantic import BaseModel


class ChangePasswordInput(BaseModel):
    old_password: str
    new_password: str


class ResetPasswordInput(BaseModel):
    user_id: UUID
    password_token_version: int
    password: str
