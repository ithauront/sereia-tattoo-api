from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies.activation import get_current_activation_context
from app.api.dependencies.auth import (
    get_current_active_user,
    get_current_admin_user,
)
from app.api.dependencies.notifications import get_email_service
from app.api.dependencies.security import get_activation_token_service
from app.api.dependencies.users import get_users_repository
from app.api.schemas.user import (
    ActivateUserRequest,
    ChangePasswordRequest,
    FirstActivationRequest,
)

from app.application.users.services.resend_activation_email_service import (
    ResendActivationEmailService,
)
from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
)
from app.core.exceptions.users import (
    InvalidActivationTokenError,
    UserActivatedBeforeError,
    UserAlreadyActivatedError,
    UserNotFoundError,
    UsernameAlreadyTakenError,
)
from app.core.exceptions.validation import ValidationError
from app.domain.notifications.handlers.send_user_activation_email import (
    SendUserActivationHandler,
)
from app.domain.users.use_cases.DTO.create_user_dto import CreateUserInput
from app.domain.users.use_cases.DTO.first_activation_user_dto import (
    FirstActivationInput,
)
from app.domain.users.use_cases.DTO.get_users_dto import (
    GetUserInput,
    ListUsersInput,
    ListUsersOutput,
    OrderBy,
    Direction,
)
from app.domain.users.use_cases.DTO.password_dto import ChangePasswordInput
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
from app.domain.users.use_cases.change_password import ChangePasswordUseCase
from app.domain.users.use_cases.create_user import CreateUserUseCase
from app.domain.users.use_cases.deactivate_user import DeactivateUserUseCase
from app.domain.users.use_cases.demote_user_from_admin import DemoteUserFromAdminUseCase
from app.domain.users.use_cases.first_activation_user import FirstActivationUserUseCase
from app.domain.users.use_cases.get_user import GetUserUseCase
from app.domain.users.use_cases.list_users import ListUsersUseCase
from app.domain.users.use_cases.promote_user_to_admin import PromoteUserToAdminUseCase
from app.domain.users.use_cases.prepare_resend_activation_email import (
    PrepareResendActivationEmailUseCase,
)


router = APIRouter()


@router.post("/users")
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
    except ValueError as exception:
        if str(exception) == "user_already_exists":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exception)
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


@router.post("/users/resend-email")
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

    except ValueError as exception:
        if str(exception) == "user_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exception)
            )
        if str(exception) == "user_has_been_activated_before":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exception)
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


# TODO: fazer teste dessa rota
@router.post("/me/first-activation")
def first_activation(
    data: FirstActivationRequest,
    current_activation_context=Depends(get_current_activation_context),
    repo=Depends(get_users_repository),
):
    use_case = FirstActivationUserUseCase(repo)
    dto = FirstActivationInput(
        user_id=current_activation_context.user_id,
        token_version=current_activation_context.token_version,
        username=data.username,
        password=data.password,
    )

    try:
        use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )
    except UserActivatedBeforeError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user_was_activated_before"
        )
    except InvalidActivationTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_activation_token"
        )
    except UsernameAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username_already_taken",
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return Response(status_code=201)


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


@router.patch("/users/deactivate/{user_id}", status_code=204)
def deactivate_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = DeactivateUserUseCase(repo)
    dto = DeactivateUserInput(user_id=user_id, actor_id=current_user.id)

    try:
        return use_case.execute(dto)
    except ValueError as exception:
        if str(exception) == "user_not_found":
            raise HTTPException(status_code=404, detail="user_not_found")
        elif str(exception) == "last_admin_cannot_be_deactivated":
            raise HTTPException(
                status_code=409, detail="last_admin_cannot_be_deactivated"
            )
        elif str(exception) == "cannot_deactivate_yourself":
            raise HTTPException(status_code=409, detail="cannot_deactivate_yourself")
        raise


@router.patch("/users/activate/{user_id}", status_code=204)
def activate_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = ActivateUserUseCase(repo)
    dto = ActivateUserInput(user_id=user_id)

    try:
        return use_case.execute(dto)
    except ValueError as exception:
        if str(exception) == "user_not_found":
            raise HTTPException(status_code=404, detail="user_not_found")
        raise


@router.patch("/users/demote/{user_id}", status_code=204)
def demote_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = DemoteUserFromAdminUseCase(repo)
    dto = DemoteUserInput(user_id=user_id, actor_id=current_user.id)

    try:
        return use_case.execute(dto)
    except ValueError as exception:
        if str(exception) == "user_not_found":
            raise HTTPException(status_code=404, detail="user_not_found")
        elif str(exception) == "last_admin_cannot_be_demoted":
            raise HTTPException(status_code=409, detail="last_admin_cannot_be_demoted")
        elif str(exception) == "cannot_demote_yourself":
            raise HTTPException(status_code=409, detail="cannot_demote_yourself")
        raise


@router.patch("/users/promote/{user_id}", status_code=204)
def promote_user(
    user_id: UUID,
    current_user=Depends(get_current_admin_user),
    repo=Depends(get_users_repository),
):
    use_case = PromoteUserToAdminUseCase(repo)
    dto = PromoteUserInput(user_id=user_id)

    try:
        return use_case.execute(dto)
    except ValueError as exception:
        if str(exception) == "user_not_found":
            raise HTTPException(status_code=404, detail="user_not_found")
        raise
