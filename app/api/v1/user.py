from uuid import UUID
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    status,
)
from app.api.dependencies.auth import (
    get_current_active_user,
    get_current_admin_user,
)
from app.api.dependencies.notifications import get_email_service
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.security import (
    get_activation_token_service,
)
from app.api.dependencies.write_unit_of_work import (
    get_write_unit_of_work,
)
from app.api.schemas.user import (
    ActivateUserRequest,
    ChangeVipClientEmailRequest,
    CreateUserRequest,
    CreateVipClientRequest,
    GenerateVipClientCodeRequest,
)
from app.application.notifications.handlers.send_user_activation_email import (
    SendUserActivationHandler,
)
from app.application.notifications.handlers.send_vip_client_creation_notification_email import (
    SendVipClientCreationNotificationEmailHandler,
)
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import (
    WriteUnitOfWork,
)
from app.application.studio.use_cases.DTO.change_email_dto import (
    ChangeVipClientEmailInput,
)
from app.application.studio.use_cases.DTO.create_user_dto import CreateUserInput
from app.application.studio.use_cases.DTO.create_vip_client_dto import (
    CreateVipClientInput,
)
from app.application.studio.use_cases.DTO.get_users_dto import (
    Direction,
    GetUserInput,
    ListUsersInput,
    ListUsersOutput,
    OrderBy,
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
from app.application.studio.use_cases.users_use_cases.change_vip_client_email import (
    ChangeVipClientEmailUseCase,
)
from app.application.studio.use_cases.users_use_cases.create_user import (
    CreateUserUseCase,
)
from app.application.studio.use_cases.users_use_cases.create_vip_client import (
    CreateVipClientUseCase,
)
from app.application.studio.use_cases.users_use_cases.deactivate_user import (
    DeactivateUserUseCase,
)
from app.application.studio.use_cases.users_use_cases.demote_user_from_admin import (
    DemoteUserFromAdminUseCase,
)
from app.application.studio.use_cases.users_use_cases.generate_vip_client_code import (
    GenerateVipClientCodeUseCase,
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
    AllClientCodesTakenError,
    CannotDeactivateYourselfError,
    CannotDemoteYourselfError,
    ClientCodeAlreadyTakenError,
    EmailAlreadyTakenError,
    LastAdminCannotBeDeactivatedError,
    LastAdminCannotBeDemotedError,
    PhoneAlreadyTakenError,
    UserActivatedBeforeError,
    UserAlreadyExistsError,
    UserNotFoundError,
    VipClientNotFoundError,
)
from app.core.exceptions.validation import ValidationError
from app.application.studio.services.client_code_generator import ClientCodeGenerator
from fastapi.concurrency import run_in_threadpool


router = APIRouter(prefix="/users")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    background_tasks: BackgroundTasks,
    data: CreateUserRequest,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    email_service=Depends(get_email_service),
    token_service=Depends(get_activation_token_service),
):
    try:
        use_case = CreateUserUseCase(uow)
        dto = CreateUserInput(user_email=data.email)

        event = await run_in_threadpool(use_case.execute, dto)

        handler = SendUserActivationHandler(
            email_service=email_service, token_service=token_service
        )

        background_tasks.add_task(handler.handle, event)

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user_already_exists"
        )

    return {
        "message": "User created if you dont recive an email please try resend email option"
    }


@router.post("/resend-email", status_code=status.HTTP_200_OK)
async def resend_email(
    background_tasks: BackgroundTasks,
    data: ActivateUserRequest,
    write_uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    email_service=Depends(get_email_service),
    token_service=Depends(get_activation_token_service),
):
    # Escolhi deixar essa rota publica porque a segurança vai estar no
    # email do usuario que foi cadastrado pelo ADMIN"
    try:
        prepare_use_case = PrepareResendActivationEmailUseCase(write_uow)
        dto = PrepareResendActivationEmailInput(user_email=data.email)

        event = await run_in_threadpool(prepare_use_case.execute, dto)

        email_handler = SendUserActivationHandler(
            email_service=email_service,
            token_service=token_service,
        )

        background_tasks.add_task(email_handler.handle, event)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )
    except UserActivatedBeforeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_has_been_activated_before",
        )

    return {"message": "Activation mail sent"}


@router.get("", status_code=status.HTTP_200_OK, response_model=ListUsersOutput)
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    is_admin: bool | None = None,
    order_by: OrderBy = OrderBy.username,
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


@router.patch("/deactivate/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.patch("/activate/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.patch("/demote/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.patch("/promote/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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


@router.patch(
    "/vip-client/change-email/{vip_client_id}", status_code=status.HTTP_204_NO_CONTENT
)
def change_vip_client_email(
    data: ChangeVipClientEmailRequest,
    vip_client_id: UUID,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = ChangeVipClientEmailUseCase(uow)
    dto = ChangeVipClientEmailInput(
        vip_client_id=vip_client_id, new_email=data.new_email
    )

    try:
        use_case.execute(dto)
    except VipClientNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="vip_client_not_found"
        )
    except EmailAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email_chosen_is_already_taken"
        )


@router.post("/vip-client/generate-client-codes", status_code=status.HTTP_200_OK)
def generate_vip_client_code_suggestions(
    data: GenerateVipClientCodeRequest,
    current_user=Depends(get_current_admin_user),
    uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
):
    generator = ClientCodeGenerator(uow)
    use_case = GenerateVipClientCodeUseCase(generator=generator)

    try:
        codes = use_case.execute(data.name)
        return {"codes": [str(code) for code in codes]}
    except AllClientCodesTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="please_try_creating_client_code_with_last_name",
        )


@router.post("/vip-client", status_code=status.HTTP_201_CREATED)
async def create_vip_client(
    background_tasks: BackgroundTasks,
    data: CreateVipClientRequest,
    current_user=Depends(get_current_admin_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    email_service=Depends(get_email_service),
):
    try:
        use_case = CreateVipClientUseCase(uow)
        dto = CreateVipClientInput(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            client_code=data.client_code,
        )

        event = await run_in_threadpool(use_case.execute, dto)

        handler = SendVipClientCreationNotificationEmailHandler(email_service)

        background_tasks.add_task(handler.handle, event)

    except EmailAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email_already_taken",
        )
    except PhoneAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="phone_already_taken",
        )
    except ClientCodeAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="client_code_already_taken_please_generate_another",
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    return {"message": "VIP Client created"}
