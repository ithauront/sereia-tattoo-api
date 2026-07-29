from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.security import get_access_token_service
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.login_dto import VerifyInput
from app.application.studio.use_cases.users_use_cases.verify_user import VerifyUserUseCase
from app.core.exceptions.security import TokenError
from app.core.security.versioned_token_service import VersionedTokenService


def get_optional_actor_id(
    authorization: Annotated[str | None, Header()] = None,
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
    access_tokens: VersionedTokenService = Depends(get_access_token_service),
):
    if authorization is None:
        return None

    use_case = VerifyUserUseCase(uow, access_tokens)

    try:
        result = use_case.execute(VerifyInput(authorization=authorization))
    except TokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    actor_id = result.user.id

    return actor_id
