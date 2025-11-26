from pydantic import BaseModel


class LoginInput(BaseModel):
    identifier: str
    password: str


class TokenOutput(BaseModel):
    access_token: str
    refresh_token: str


class RefreshInput(BaseModel):
    refresh_token: str
