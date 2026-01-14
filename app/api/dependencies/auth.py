from uuid import UUID
from fastapi import Depends, HTTPException, Header, status

from app.api.dependencies.users import get_users_repository
from app.core.exceptions.security import TokenError
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.verify_user import VerifyUserUseCase

from app.domain.users.use_cases.DTO.login_dto import VerifyInput


def get_current_user(
    authorization: str = Header(...),
    repo: UsersRepository = Depends(get_users_repository),
):
    use_case = VerifyUserUseCase(repo)

    try:
        result = use_case.execute(VerifyInput(authorization=authorization))
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    user = repo.find_by_id(UUID(result.sub))

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
