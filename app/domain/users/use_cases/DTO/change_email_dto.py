from pydantic import BaseModel, EmailStr


class ChangeEmailInput(BaseModel):
    password: str
    new_email: EmailStr
