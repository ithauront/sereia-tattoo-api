from pydantic import BaseModel, EmailStr


class PrepareResendActivationEmailInput(BaseModel):
    user_email: EmailStr
