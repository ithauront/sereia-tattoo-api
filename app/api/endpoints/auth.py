from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jose import JWTError
from app.schemas.auth import TokenPair, LoginRequest, RefreshRequest
from app.api.deps import get_db
from app.db.models.users import User
from app.core.security import verify_password, create_token, require_token
from app.core.config import settings

router = APIRouter()


@router.post("/auth/login", response_model=TokenPair)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user: Optional[User] = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="incorect username or password",
        )

    access = create_token(
        subject=user.username,
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )
    refresh = create_token(
        subject=user.username,
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        token_type="refresh",
    )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        payload = require_token(data.refresh_token, expected_type="refresh")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token"
        )

    username = payload["sub"]
    user: Optional[User] = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
        )
    access = create_token(
        subject=user.username,
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )
    new_refresh = create_token(
        subject=user.username,
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        token_type="refresh",
    )
    return TokenPair(access_token=access, refresh_token=new_refresh)


@router.get("/auth/verify")
def verify(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token"
        )
    token = authorization.split(" ", 1)[1]

    try:
        payload = require_token(token, expected_type="access")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )
    return {"valid": True, "sub": payload.get("sub"), "type": payload.get("type")}
