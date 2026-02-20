from uuid import UUID
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from app.api.dependencies.auth import (
    get_current_active_user,
    get_current_admin_user,
)
from app.api.dependencies.notifications import get_email_service
from app.api.dependencies.security import (
    get_activation_token_service,
)
from app.api.dependencies.users import get_users_repository
from app.api.dependencies.vip_clients import get_vip_clients_repository
from app.api.schemas.user import (
    ActivateUserRequest,
    ChangeVipClientEmailRequest,
    CreateVipClientRequest,
    GenerateVipClientCodeRequest,
)
from app.application.users.services.resend_activation_email_service import (
    ResendActivationEmailService,
)
from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
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
from app.domain.notifications.handlers.send_user_activation_email import (
    SendUserActivationHandler,
)
from app.domain.notifications.handlers.send_vip_client_creation_notification_email import (
    SendVipClientCreationNotificationEmailHandler,
)
from app.domain.users.services.client_code_generator import ClientCodeGenerator
from app.domain.users.use_cases.DTO.change_email_dto import ChangeVipClientEmailInput
from app.domain.users.use_cases.DTO.create_user_dto import CreateUserInput
from app.domain.users.use_cases.DTO.create_vip_client_dto import CreateVipClientInput
from app.domain.users.use_cases.DTO.get_users_dto import (
    GetUserInput,
    ListUsersInput,
    ListUsersOutput,
    OrderBy,
    Direction,
)
from app.domain.users.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.domain.users.use_cases.DTO.user_output_dto import UserOutput
from app.domain.users.use_cases.DTO.user_status_dto import (
    ActivateUserInput,
    DeactivateUserInput,
    DemoteUserInput,
    PromoteUserInput,
)
from app.domain.users.use_cases.activate_user import ActivateUserUseCase
from app.domain.users.use_cases.change_vip_client_email import (
    ChangeVipClientEmailUseCase,
)
from app.domain.users.use_cases.create_user import CreateUserUseCase
from app.domain.users.use_cases.create_vip_client import CreateVipClientUseCase
from app.domain.users.use_cases.deactivate_user import DeactivateUserUseCase
from app.domain.users.use_cases.demote_user_from_admin import DemoteUserFromAdminUseCase
from app.domain.users.use_cases.generate_vip_client_code import (
    GenerateVipClientCodeUseCase,
)
from app.domain.users.use_cases.get_user import GetUserUseCase
from app.domain.users.use_cases.list_users import ListUsersUseCase
from app.domain.users.use_cases.promote_user_to_admin import PromoteUserToAdminUseCase
from app.domain.users.use_cases.prepare_resend_activation_email import (
    PrepareResendActivationEmailUseCase,
)


router = APIRouter(prefix="/users")


# TODO: verificar e padronizar os status e os retornos no caso de sucesso de todas as rotas.
@router.post("")
async def create_user(
    data: ActivateUserRequest,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
    email_service=Depends(get_email_service),
    token_service=Depends(get_activation_token_service),
):
    try:
        use_case = CreateUserUseCase(repo)
        dto = CreateUserInput(user_email=data.email)
        event = use_case.execute(dto)

        handler = SendUserActivationHandler(
            email_service=email_service, token_service=token_service
        )
        await handler.handle(event)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user_already_exists"
        )
    except EmailServiceUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="email_service_unavailable"
        )
    except EmailSentFailedError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="email_send_failed",
        )

    return {"message": "User created and activation mail sent"}


@router.post("/resend-email")
async def resend_email(
    data: ActivateUserRequest,
    repo=Depends(get_users_repository),
    email_service=Depends(get_email_service),
    token_service=Depends(get_activation_token_service),
):
    # Escolhi deixar essa rota publica porque a segurança vai estar no
    # email do usuario que foi cadastrado pelo ADMIN"
    try:
        prepare_use_case = PrepareResendActivationEmailUseCase(repo)

        email_handler = SendUserActivationHandler(
            email_service=email_service,
            token_service=token_service,
        )

        service = ResendActivationEmailService(
            repo=repo,
            prepare_use_case=prepare_use_case,
            email_handler=email_handler,
        )
        dto = PrepareResendActivationEmailInput(user_email=data.email)

        await service.execute(dto)

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )
    except UserActivatedBeforeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="user_has_been_activated_before",
        )
    except EmailServiceUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="email_service_unavailable"
        )
    except EmailSentFailedError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="email_send_failed",
        )

    return {"message": "Activation mail sent"}


@router.get("", response_model=ListUsersOutput)
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


@router.get("/{user_id}", response_model=UserOutput)
def get_user(
    user_id: UUID,
    current_user=Depends(get_current_active_user),
    repo=Depends(get_users_repository),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")

    use_case = GetUserUseCase(repo)
    dto = GetUserInput(user_id=user_id)

    try:
        return use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )


@router.patch("/deactivate/{user_id}", status_code=204)
def deactivate_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = DeactivateUserUseCase(repo)
    dto = DeactivateUserInput(user_id=user_id, actor_id=current_user.id)

    try:
        return use_case.execute(dto)
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


@router.patch("/activate/{user_id}", status_code=204)
def activate_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = ActivateUserUseCase(repo)
    dto = ActivateUserInput(user_id=user_id)

    try:
        return use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )


@router.patch("/demote/{user_id}", status_code=204)
def demote_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = DemoteUserFromAdminUseCase(repo)
    dto = DemoteUserInput(user_id=user_id, actor_id=current_user.id)

    try:
        return use_case.execute(dto)
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


@router.patch("/promote/{user_id}", status_code=204)
def promote_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = PromoteUserToAdminUseCase(repo)
    dto = PromoteUserInput(user_id=user_id)

    try:
        return use_case.execute(dto)
    except UserNotFoundError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )


@router.patch("/vip-client/change-email/{vip_client_id}")
def change_vip_client_email(
    data: ChangeVipClientEmailRequest,
    vip_client_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_vip_clients_repository),
):
    use_case = ChangeVipClientEmailUseCase(repo)
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
    return Response(status_code=204)


@router.post("/vip-client/generate-client-codes", status_code=status.HTTP_200_OK)
def generate_vip_client_code_suggestions(
    data: GenerateVipClientCodeRequest,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_vip_clients_repository),
):
    generator = ClientCodeGenerator(repo)
    use_case = GenerateVipClientCodeUseCase(generator=generator)

    try:
        codes = use_case.execute(data.name)
        return {"codes": [str(code) for code in codes]}
    except AllClientCodesTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="please_try_creating_client_code_with_last_name",
        )


# fazer testes dessa rota inclusive verificar se a criação falhar o email não deve ir
@router.post("/vip-client")
async def create_vip_client(
    background_tasks: BackgroundTasks,
    data: CreateVipClientRequest,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_vip_clients_repository),
    email_service=Depends(get_email_service),
):
    try:
        use_case = CreateVipClientUseCase(repo)
        dto = CreateVipClientInput(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            client_code=data.client_code,
        )

        event = use_case.execute(dto)

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
