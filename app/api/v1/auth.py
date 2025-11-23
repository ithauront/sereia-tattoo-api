from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jose import JWTError
from app.api.deps import get_db
from app.api.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.core.config import settings
from app.domain.users.use_cases.DTO.login_dto import LoginInput
from app.domain.users.use_cases.login_user import LoginUserUseCase
from app.infrastructure.sqlalchemy.models.users import UserModel
from app.core.security import jwt_service
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)


router = APIRouter()


# TODO mover a logica para um useCase em users e aqui so chamar o usecase. talvez
# mover a criação de hash e token para pasta crypto e tokens em infra, ou
# deixar em domain config e security como esta
# o usecase vai chamar o hash e vai devolver o token, se eu não me engano
@router.post("/auth/login", response_model=TokenPair)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    repo = SQLAlchemyUsersRepository(session=db)
    use_case = LoginUserUseCase(repo)
    use_case_input = LoginInput(identifier=data.identifier, password=data.password)
    try:
        result = use_case.execute(use_case_input)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_credentials"
        )

    return TokenPair(
        access_token=result.access_token, refresh_token=result.refresh_token
    )


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        payload = jwt_service.verify(data.refresh_token, expected_type="refresh")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token"
        )

    username = payload["sub"]
    user: Optional[UserModel] = (
        db.query(UserModel).filter(UserModel.username == username).first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
        )
    access = jwt_service.create(
        subject=user.username,
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )
    new_refresh = jwt_service.create(
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
        payload = jwt_service.verify(token, expected_type="access")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )
    return {"valid": True, "sub": payload.get("sub"), "type": payload.get("type")}
