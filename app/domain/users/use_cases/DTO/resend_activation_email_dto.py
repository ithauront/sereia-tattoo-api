from pydantic import BaseModel


class ResendActivationEmailInput(BaseModel):
    user_email: str
