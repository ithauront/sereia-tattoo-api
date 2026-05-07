from uuid import UUID

from pydantic import BaseModel, EmailStr


class CreateUserInput(BaseModel):
    user_email: EmailStr
    actor_id: UUID
