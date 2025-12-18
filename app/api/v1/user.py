from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies.auth import get_current_active_user, get_current_admin_user
from app.api.dependencies.users import get_users_repository
from app.api.schemas.user import ChangePasswordRequest

from app.domain.users.use_cases.DTO.get_users_dto import (
    GetUserInput,
    ListUsersInput,
    ListUsersOutput,
    OrderBy,
    Direction,
)
from app.domain.users.use_cases.DTO.password_dto import ChangePasswordInput
from app.domain.users.use_cases.DTO.user_output_dto import UserOutput
from app.domain.users.use_cases.change_password import ChangePasswordUseCase
from app.domain.users.use_cases.get_user import GetUserUseCase
from app.domain.users.use_cases.list_users import ListUsersUseCase


router = APIRouter()


@router.post("/me/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user=Depends(get_current_active_user),
    repo=Depends(get_users_repository),
):
    use_case = ChangePasswordUseCase(repo)
    dto = ChangePasswordInput(
        old_password=data.old_password, new_password=data.new_password
    )

    try:
        use_case.execute(dto, current_user)
    except ValueError as exception:
        if str(exception) == "invalid_credentials":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
            )

    return Response(status_code=204)


@router.get("/admin/users", response_model=ListUsersOutput)
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    is_admin: bool | None = None,
    order_by: OrderBy = OrderBy.username,
    direction: Direction = Direction.asc,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = ListUsersUseCase(repo)
    dto = ListUsersInput(
        is_active=is_active,
        is_admin=is_admin,
        page=page,
        limit=limit,
        order_by=order_by,
        direction=direction,
    )

    result = use_case.execute(dto)

    return result


@router.get("/users/{user_id}", response_model=UserOutput)
def get_user(
    user_id: UUID,
    current_user=Depends(get_current_active_user),
    repo=Depends(get_users_repository),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="forbidden")

    use_case = GetUserUseCase(repo)
    dto = GetUserInput(user_id=user_id)

    try:
        return use_case.execute(dto)
    except ValueError as exception:
        if str(exception) == "user_not_found":
            raise HTTPException(status_code=404, detail="user_not_found")
        raise
