from uuid import UUID
from pydantic import BaseModel, EmailStr


class ChangeEmailInput(BaseModel):
    password: str
    new_email: EmailStr


class ChangeVipClientEmailInput(BaseModel):
    vip_client_id: UUID
    new_email: EmailStr
