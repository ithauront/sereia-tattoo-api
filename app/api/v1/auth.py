from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.api.dependencies.users import get_users_repository
from app.api.schemas.auth import LoginRequest, RefreshRequest, TokenPair, VerifyResponse
from app.core.exceptions.users import AuthenticationFailedError, UserInactiveError
from app.domain.users.use_cases.DTO.login_dto import (
    LoginInput,
    RefreshInput,
    VerifyInput,
)
from app.domain.users.use_cases.login_user import LoginUserUseCase
from app.domain.users.use_cases.refresh_user import RefreshUserUseCase
from app.domain.users.use_cases.verify_user import VerifyUserUseCase


router = APIRouter()


@router.post("/auth/login", response_model=TokenPair)
def login(data: LoginRequest, repo=Depends(get_users_repository)) -> TokenPair:
    use_case = LoginUserUseCase(repo)
    use_case_input = LoginInput(identifier=data.identifier, password=data.password)
    try:
        result = use_case.execute(use_case_input)
    except UserInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="inactive_user"
        )
    except AuthenticationFailedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    return TokenPair(
        access_token=result.access_token, refresh_token=result.refresh_token
    )


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, repo=Depends(get_users_repository)) -> TokenPair:
    use_case = RefreshUserUseCase(repo)
    use_case_input = RefreshInput(refresh_token=data.refresh_token)
    try:
        result = use_case.execute(use_case_input)
    except AuthenticationFailedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    return TokenPair(
        access_token=result.access_token, refresh_token=result.refresh_token
    )


@router.get("/auth/verify")
def verify(
    authorization: str = Header(...), repo=Depends(get_users_repository)
) -> VerifyResponse:
    use_case = VerifyUserUseCase(repo)
    use_case_input = VerifyInput(authorization=authorization)

    try:
        result = use_case.execute(use_case_input)
    except AuthenticationFailedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    return VerifyResponse(valid=result.valid, sub=result.sub, token_type=result.type)
