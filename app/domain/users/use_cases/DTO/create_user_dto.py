from pydantic import BaseModel, EmailStr


class CreateUserInput(BaseModel):
    user_email: EmailStr
