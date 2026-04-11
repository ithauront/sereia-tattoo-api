from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ChangeEmailRequest(BaseModel):
    password: str
    new_email: EmailStr


class CreateUserRequest(BaseModel):
    email: EmailStr


class CreateUserResponse(BaseModel):
    message: str


class ActivateUserRequest(BaseModel):
    email: EmailStr


class SendActivationEmailRequest(BaseModel):
    user_id: UUID
    email: str
    activation_token_version: int


class FirstActivationRequest(BaseModel):
    username: str
    password: str


class ResetPasswordEmailRequest(BaseModel):
    email: EmailStr


class ResetPasswordEmailResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    new_password: str


class ChangeVipClientEmailRequest(BaseModel):
    new_email: EmailStr


class ChangeVipClientPhoneRequest(BaseModel):
    new_phone: str


class GenerateVipClientCodeRequest(BaseModel):
    name: str


class CreateVipClientRequest(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    client_code: str


class CreateVipClientResponse(BaseModel):
    message: str


class GenerateVipClientCodeResponse(BaseModel):
    codes: List[str]


class ResendActivationEmailResponse(BaseModel):
    message: str
