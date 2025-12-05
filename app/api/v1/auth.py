from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.schemas.auth import LoginRequest, RefreshRequest, TokenPair, VerifyResponse
from app.domain.users.use_cases.DTO.login_dto import (
    LoginInput,
    RefreshInput,
    VerifyInput,
)
from app.domain.users.use_cases.login_user import LoginUserUseCase
from app.domain.users.use_cases.refresh_user import RefreshUserUseCase
from app.domain.users.use_cases.verify_user import VerifyUserUseCase
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)


router = APIRouter()


@router.post("/auth/login", response_model=TokenPair)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    repo = SQLAlchemyUsersRepository(session=db)
    use_case = LoginUserUseCase(repo)
    use_case_input = LoginInput(identifier=data.identifier, password=data.password)
    try:
        result = use_case.execute(use_case_input)
    except ValueError as exception:
        if str(exception) == "inactive_user":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="inactive_user"
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    return TokenPair(
        access_token=result.access_token, refresh_token=result.refresh_token
    )


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    repo = SQLAlchemyUsersRepository(session=db)
    use_case = RefreshUserUseCase(repo)
    use_case_input = RefreshInput(refresh_token=data.refresh_token)
    try:
        result = use_case.execute(use_case_input)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    return TokenPair(
        access_token=result.access_token, refresh_token=result.refresh_token
    )


@router.get("/auth/verify")
def verify(
    authorization: str = Header(...), db: Session = Depends(get_db)
) -> VerifyResponse:
    repo = SQLAlchemyUsersRepository(session=db)
    use_case = VerifyUserUseCase(repo)
    use_case_input = VerifyInput(authorization=authorization)

    try:
        result = use_case.execute(use_case_input)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    return VerifyResponse(valid=result.valid, sub=result.sub, token_type=result.type)
