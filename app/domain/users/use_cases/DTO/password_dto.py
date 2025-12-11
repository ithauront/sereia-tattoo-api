from pydantic import BaseModel


class ChangePasswordInput(BaseModel):
    old_password: str
    new_password: str
