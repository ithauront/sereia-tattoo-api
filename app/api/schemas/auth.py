from pydantic import BaseModel


class LoginRequest(BaseModel):
    identifier: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerifyResponse(BaseModel):
    valid: bool
    sub: str
    token_type: str
