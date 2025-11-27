import enum
from pydantic import BaseModel


class LoginInput(BaseModel):
    identifier: str
    password: str


class TokenOutput(BaseModel):
    access_token: str
    refresh_token: str


class RefreshInput(BaseModel):
    refresh_token: str


class VerifyInput(BaseModel):
    authorization: str


class TokenType(str, enum.Enum):
    access = "access"
    refresh = "refresh"


class VerifyOutput(BaseModel):
    valid: bool
    sub: str
    type: TokenType
