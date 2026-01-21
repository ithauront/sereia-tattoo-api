from pydantic import BaseModel


class PrepareSendForgotPasswordEmailInput(BaseModel):
    user_email: str
