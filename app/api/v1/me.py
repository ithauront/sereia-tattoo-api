from app.api.dependencies.events import get_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.security import (
    get_access_token_service,
    get_refresh_token_service,
)
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.api.schemas.auth import TokenPair
from app.application.event_bus.event_bus import EventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.change_email_dto import ChangeEmailInput
from app.application.studio.use_cases.DTO.first_activation_user_dto import (
    FirstActivationInput,
)
from app.application.studio.use_cases.DTO.login_dto import LoginInput
from app.application.studio.use_cases.DTO.password_dto import (
    ChangePasswordInput,
    ResetPasswordInput,
)
from app.application.studio.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)
from app.application.studio.use_cases.users_use_cases.change_email import (
    ChangeEmailUseCase,
)
from app.application.studio.use_cases.users_use_cases.change_password import (
    ChangePasswordUseCase,
)
from app.application.studio.use_cases.users_use_cases.first_activation_user import (
    FirstActivationUserUseCase,
)
from app.application.studio.use_cases.users_use_cases.login_user import LoginUserUseCase
from app.application.studio.use_cases.users_use_cases.prepare_send_forgot_password_email import (
    PrepareSendForgotPasswordEmailUseCase,
)
from app.application.studio.use_cases.users_use_cases.reset_password import (
    ResetPasswordUseCase,
)
from app.core.exceptions.validation import ValidationError
from app.core.exceptions.users import (
    AuthenticationFailedError,
    EmailAlreadyTakenError,
    InvalidActivationTokenError,
    InvalidPasswordTokenError,
    UserActivatedBeforeError,
    UserInactiveError,
    UserNotFoundError,
    UsernameAlreadyTakenError,
)
from app.core.security.activation_context import ActivationContext
from app.core.security.password_context import PasswordContext
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.dependencies.token_context import (
    get_current_activation_context,
    get_current_reset_password_context,
)
from app.api.schemas.user import (
    ChangeEmailRequest,
    ChangePasswordRequest,
    FirstActivationRequest,
    ResetPasswordEmailRequest,
    ResetPasswordEmailResponse,
    ResetPasswordRequest,
)
from app.api.dependencies.auth import (
    get_current_active_user,
)
from app.core.security.versioned_token_service import VersionedTokenService

router = APIRouter(prefix="/me")


@router.post(
    "/first-activation", status_code=status.HTTP_200_OK, response_model=TokenPair
)
def first_activation(
    data: FirstActivationRequest,
    current_activation_context: ActivationContext = Depends(
        get_current_activation_context
    ),
    write_uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    read_uow: ReadUnitOfWork = Depends(get_read_unit_of_work),
    access_tokens: VersionedTokenService = Depends(get_access_token_service),
    refresh_tokens: VersionedTokenService = Depends(get_refresh_token_service),
) -> TokenPair:
    """
    This route first calls the FirstActivationUserUseCase to complete the user's
    initial account activation.

    After a successful activation, it calls the LoginUserUseCase to generate and
    return a TokenPair to the frontend, providing a better user experience by
    automatically logging the user in.

    We assume that if the activation flow completes successfully, the login step
    cannot fail. If an error occurs during login at this point, it likely indicates
    an unexpected server-side issue.
    """
    use_case = FirstActivationUserUseCase(write_uow)
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    login_dto = LoginInput(identifier=data.username, password=data.password)
    login_use_case = LoginUserUseCase(
        access_tokens=access_tokens, refresh_tokens=refresh_tokens, uow=read_uow
    )
    tokens = login_use_case.execute(login_dto)
    return TokenPair(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.patch("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: ChangePasswordRequest,
    current_user=Depends(get_current_active_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = ChangePasswordUseCase(uow)
    dto = ChangePasswordInput(
        old_password=data.old_password,
        new_password=data.new_password,
        user_id=current_user.id,
    )
    """
    In use_case we have an exception for user_not_found that is untreated in route.
    This is expected because the userid in this route is already validate in dependency.
    We kept the user_not_found error in use_case as a placeholder for a business rule.
    """

    try:
        use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )
    except AuthenticationFailedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )


@router.patch("/change-email", status_code=status.HTTP_204_NO_CONTENT)
def change_email(
    data: ChangeEmailRequest,
    current_user=Depends(get_current_active_user),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = ChangeEmailUseCase(uow)
    dto = ChangeEmailInput(
        password=data.password, new_email=data.new_email, user_id=current_user.id
    )
    """
    In use_case we have an exception for user_not_found that is untreated in route.
    This is expected because the userid in this route is already validate in dependency.
    We kept the user_not_found error in use_case as a placeholder for a business rule.
    """

    try:
        use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="invalid_credentials"
        )
    except AuthenticationFailedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="invalid_credentials"
        )
    except EmailAlreadyTakenError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email_chosen_is_already_taken"
        )


@router.post(
    "/reset-password-request",
    status_code=status.HTTP_200_OK,
    response_model=ResetPasswordEmailResponse,
)
async def send_reset_password(
    data: ResetPasswordEmailRequest,
    write_uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
    event_bus: EventBus = Depends(get_event_bus),
):
    try:
        prepare_use_case = PrepareSendForgotPasswordEmailUseCase(write_uow, event_bus)
        dto = PrepareSendForgotPasswordEmailInput(user_email=data.email)

        await prepare_use_case.execute(dto)

    except (UserNotFoundError, UserInactiveError):
        # retornamos 200 com uma msg generica para não dar info
        return {
            "message": "if user exists and is active a link was sent to reset password"
        }

    return {"message": "if user exists and is active a link was sent to reset password"}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    data: ResetPasswordRequest,
    current_password_context: PasswordContext = Depends(
        get_current_reset_password_context
    ),
    uow: WriteUnitOfWork = Depends(get_write_unit_of_work),
):
    use_case = ResetPasswordUseCase(uow)
    dto = ResetPasswordInput(
        user_id=current_password_context.user_id,
        password_token_version=current_password_context.token_version,
        password=data.new_password,
    )

    try:
        use_case.execute(dto)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found"
        )
    except UserInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="user_inactive"
        )
    except InvalidPasswordTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_activation_token"
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )
