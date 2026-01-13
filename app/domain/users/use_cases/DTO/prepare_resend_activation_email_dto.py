from pydantic import BaseModel


class PrepareResendActivationEmailInput(BaseModel):
    user_email: str
