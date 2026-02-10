from pydantic import BaseModel


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ChangeEmailRequest(BaseModel):
    password: str
    new_email: str


class ActivateUserRequest(BaseModel):
    email: str


class FirstActivationRequest(BaseModel):
    username: str
    password: str


class ResetPasswordEmailRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    new_password: str
