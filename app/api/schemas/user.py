from pydantic import BaseModel


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ActivateUserRequest(BaseModel):
    email: str
