from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from app.api.dependencies.auth import (
    get_current_active_user,
    get_current_admin_user,
)
from app.api.dependencies.events import get_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import (
    get_write_unit_of_work,
)
from app.api.schemas.user import (
    ActivateUserRequest,
    CreateUserRequest,
    CreateUserResponse,
    ResendActivationEmailResponse,
)
from app.application.event_bus.event_bus import EventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import (
    WriteUnitOfWork,
)
from app.application.studio.use_cases.DTO.commun import Direction
from app.application.studio.use_cases.DTO.create_user_dto import CreateUserInput
from app.application.studio.use_cases.DTO.get_users_dto import (
    GetUserInput,
    ListUsersInput,
    ListUsersOutput,
    UsersOrderBy,
)
from app.application.studio.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.application.studio.use_cases.DTO.user_output_dto import UserOutput
from app.application.studio.use_cases.DTO.user_status_dto import (
    ActivateUserInput,
    DeactivateUserInput,
    DemoteUserInput,
    PromoteUserInput,
)
from app.application.studio.use_cases.users_use_cases.activate_user import (
    ActivateUserUseCase,
)
from app.application.studio.use_cases.users_use_cases.create_user import (
    CreateUserUseCase,
)
from app.application.studio.use_cases.users_use_cases.deactivate_user import (
    DeactivateUserUseCase,
)
from app.application.studio.use_cases.users_use_cases.demote_user_from_admin import (
    DemoteUserFromAdminUseCase,
)
from app.application.studio.use_cases.users_use_cases.get_user import GetUserUseCase
from app.application.studio.use_cases.users_use_cases.list_users import ListUsersUseCase
from app.application.studio.use_cases.users_use_cases.prepare_resend_activation_email import (
    PrepareResendActivationEmailUseCase,
)
from app.application.studio.use_cases.users_use_cases.promote_user_to_admin import (
    PromoteUserToAdminUseCase,
)
from app.core.exceptions.users import (
    CannotDeactivateYourselfError,
    CannotDemoteYourselfError,
    LastAdminCannotBeDeactivatedError,
    LastAdminCannotBeDemotedError,
    UserActivatedBeforeError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


router = APIRouter(prefix="/users")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateUserResponse)
async def create_user(
    data: CreateUserRequest,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    event_bus: EventBus = Depends(get_event_bus),
):
    try:
        use_case = CreateUserUseCase(uow, event_bus)
        dto = CreateUserInput(user_email=data.email)

        await use_case.execute(dto)

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user_already_exists"
        )

    return {
        "message": "User created if you dont recive an email please try resend email option"
    }


@router.post(
    "/resend-email",
    status_code=status.HTTP_200_OK,
    response_model=ResendActivationEmailResponse,
)
async def resend_email(
    data: ActivateUserRequest,
    write_uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    event_bus: EventBus = Depends(get_event_bus),
):
    # Escolhi deixar essa rota publica porque a segurança vai estar no
    # email do usuario que foi cadastrado pelo ADMIN"
    try:
        prepare_use_case = PrepareResendActivationEmailUseCase(write_uow, event_bus)
        dto = PrepareResendActivationEmailInput(user_email=data.email)

        await prepare_use_case.execute(dto)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )
    except UserActivatedBeforeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_has_been_activated_before",
        )

    return {"message": "Activation email request accepted"}


@router.get("", status_code=status.HTTP_200_OK, response_model=ListUsersOutput)
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    is_admin: bool | None = None,
    order_by: UsersOrderBy = UsersOrderBy.username,
    direction: Direction = Direction.asc,
    current_user=Depends(get_current_admin_user),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    use_case = ListUsersUseCase(uow)
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


@router.get("/{user_id}", status_code=status.HTTP_200_OK, response_model=UserOutput)
def get_user(
    user_id: UUID,
    current_user=Depends(get_current_active_user),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    use_case = GetUserUseCase(uow)
    dto = GetUserInput(user_id=user_id)

    try:
        return use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )


@router.patch("/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = DeactivateUserUseCase(uow)
    dto = DeactivateUserInput(user_id=user_id, actor_id=current_user.id)

    try:
        use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )
    except LastAdminCannotBeDeactivatedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="last_admin_cannot_be_deactivated",
        )
    except CannotDeactivateYourselfError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="cannot_deactivate_yourself"
        )


@router.patch("/{user_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
def activate_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = ActivateUserUseCase(uow)
    dto = ActivateUserInput(user_id=user_id)

    try:
        use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )


@router.patch("/{user_id}/demote", status_code=status.HTTP_204_NO_CONTENT)
def demote_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = DemoteUserFromAdminUseCase(uow)
    dto = DemoteUserInput(user_id=user_id, actor_id=current_user.id)

    try:
        use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )
    except LastAdminCannotBeDemotedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="last_admin_cannot_be_demoted"
        )
    except CannotDemoteYourselfError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="cannot_demote_yourself"
        )


@router.patch("/{user_id}/promote", status_code=status.HTTP_204_NO_CONTENT)
def promote_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = PromoteUserToAdminUseCase(uow)
    dto = PromoteUserInput(user_id=user_id)

    try:
        use_case.execute(dto)
    except UserNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )
