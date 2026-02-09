from pydantic import BaseModel, EmailStr


class PrepareSendForgotPasswordEmailInput(BaseModel):
    user_email: EmailStr
