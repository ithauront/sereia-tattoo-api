from fastapi import Depends, HTTPException, Header, status
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.security import get_access_token_service
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.login_dto import VerifyInput
from app.application.studio.use_cases.users_use_cases.verify_user import (
    VerifyUserUseCase,
)
from app.core.exceptions.security import TokenError
from app.core.security.versioned_token_service import VersionedTokenService


def get_current_user(
    authorization: str = Header(...),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
    access_tokens: VersionedTokenService = Depends(get_access_token_service),
):
    use_case = VerifyUserUseCase(uow, access_tokens)

    try:
        result = use_case.execute(VerifyInput(authorization=authorization))
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    user = result.user

    return user


def get_current_active_user(user=Depends(get_current_user)):
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="inactive_user"
        )
    return user


def get_current_admin_user(user=Depends(get_current_active_user)):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return user
