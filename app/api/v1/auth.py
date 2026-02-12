from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.security import (
    get_access_token_service,
    get_refresh_token_service,
)
from app.api.dependencies.users import get_users_repository
from app.api.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.core.exceptions.security import TokenError
from app.core.exceptions.users import (
    AuthenticationFailedError,
    UserInactiveError,
)
from app.core.security.versioned_token_service import VersionedTokenService
from app.domain.users.use_cases.DTO.login_dto import (
    LoginInput,
    LogoutInput,
    RefreshInput,
)
from app.domain.users.use_cases.login_user import LoginUserUseCase
from app.domain.users.use_cases.logout_user import LogoutUserUseCase
from app.domain.users.use_cases.refresh_user import RefreshUserUseCase


router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenPair)
def login(
    data: LoginRequest,
    repo=Depends(get_users_repository),
    access_tokens: VersionedTokenService = Depends(get_access_token_service),
    refresh_tokens: VersionedTokenService = Depends(get_refresh_token_service),
) -> TokenPair:
    use_case = LoginUserUseCase(repo, access_tokens, refresh_tokens)
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


@router.post("/logout")
def logout_user(
    current_user=Depends(get_current_user),
    repo=Depends(get_users_repository),
):
    user_id = current_user.id
    use_case = LogoutUserUseCase(repo)

    dto = LogoutInput(user_id=user_id)
    use_case.execute(dto)
    """
    Apesar do use_case retornar um possivel user_not_found nos não vamos tratar esse erro
    A dependency ja trata o caso de user_not_found e retorna um 401 token invalid
    Caso a gente tratasse o user_not_found do use case
    nos teriamos inconsistencia nos retornos desse erro (401 vs 404)
    """

    return Response(status_code=204)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    data: RefreshRequest,
    repo=Depends(get_users_repository),
    access_tokens: VersionedTokenService = Depends(get_access_token_service),
    refresh_tokens: VersionedTokenService = Depends(get_refresh_token_service),
) -> TokenPair:
    use_case = RefreshUserUseCase(repo, refresh_tokens, access_tokens)
    use_case_input = RefreshInput(refresh_token=data.refresh_token)
    try:
        result = use_case.execute(use_case_input)
    except AuthenticationFailedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )
    except TokenError as exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=exception.message
        )

    return TokenPair(
        access_token=result.access_token, refresh_token=result.refresh_token
    )
