from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.security import (
    get_access_token_service,
    get_refresh_token_service,
)
from app.api.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.login_dto import (
    LoginInput,
    LogoutInput,
    RefreshInput,
)
from app.application.studio.use_cases.users_use_cases.login_user import LoginUserUseCase
from app.application.studio.use_cases.users_use_cases.logout_user import (
    LogoutUserUseCase,
)
from app.application.studio.use_cases.users_use_cases.refresh_user import (
    RefreshUserUseCase,
)
from app.core.exceptions.security import TokenError
from app.core.exceptions.users import (
    AuthenticationFailedError,
    UserInactiveError,
)
from app.core.security.versioned_token_service import VersionedTokenService


router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenPair)
def login(
    data: LoginRequest,
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
    access_tokens: VersionedTokenService = Depends(get_access_token_service),
    refresh_tokens: VersionedTokenService = Depends(get_refresh_token_service),
) -> TokenPair:
    use_case = LoginUserUseCase(uow, access_tokens, refresh_tokens)
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
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    user_id = current_user.id
    use_case = LogoutUserUseCase(uow)

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
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
    access_tokens: VersionedTokenService = Depends(get_access_token_service),
    refresh_tokens: VersionedTokenService = Depends(get_refresh_token_service),
) -> TokenPair:
    use_case = RefreshUserUseCase(uow, refresh_tokens, access_tokens)
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
