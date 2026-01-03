from pydantic import BaseModel


class CreateUserInput(BaseModel):
    user_email: str
