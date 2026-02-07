from app.api.dependencies.notifications import get_email_service
from app.api.dependencies.users import get_users_repository
from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
)
from app.core.exceptions.validation import ValidationError
from app.core.exceptions.users import (
    AuthenticationFailedError,
    InvalidActivationTokenError,
    InvalidPasswordTokenError,
    UserActivatedBeforeError,
    UserInactiveError,
    UserNotFoundError,
    UsernameAlreadyTakenError,
)
from app.core.security.activation_context import ActivationContext
from app.core.security.password_context import PasswordContext
from app.domain.users.use_cases.DTO.first_activation_user_dto import (
    FirstActivationInput,
)
from app.domain.users.use_cases.first_activation_user import FirstActivationUserUseCase
from app.domain.users.use_cases.prepare_send_forgot_password_email import (
    PrepareSendForgotPasswordEmailUseCase,
)
from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.api.dependencies.token_context import (
    get_current_activation_context,
    get_current_reset_password_context,
)
from app.api.dependencies.security import (
    get_reset_password_token_service,
)
from app.api.schemas.user import (
    ChangePasswordRequest,
    FirstActivationRequest,
    ResetPasswordEmailRequest,
    ResetPasswordRequest,
)
from app.domain.users.use_cases.change_password import ChangePasswordUseCase
from app.domain.users.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)
from app.domain.users.use_cases.DTO.password_dto import (
    ChangePasswordInput,
    ResetPasswordInput,
)
from app.application.users.services.send_password_reset_email_service import (
    SendPasswordResetEmailService,
)
from app.domain.notifications.handlers.send_password_reset_email import (
    SendPasswordResetEmailHandler,
)
from app.api.dependencies.auth import (
    get_current_active_user,
)
from app.domain.users.use_cases.reset_password import ResetPasswordUseCase

router = APIRouter(prefix="/me")


@router.post("/first-activation")
def first_activation(
    data: FirstActivationRequest,
    current_activation_context: ActivationContext = Depends(
        get_current_activation_context
    ),
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
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        )

    return Response(status_code=201)


@router.post("/change-password")
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
    except AuthenticationFailedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials"
        )

    return Response(status_code=204)


@router.post("/reset-password-request")
async def send_reset_password(
    data: ResetPasswordEmailRequest,
    repo=Depends(get_users_repository),
    email_service=Depends(get_email_service),
    token_service=Depends(get_reset_password_token_service),
):
    try:
        prepare_use_case = PrepareSendForgotPasswordEmailUseCase(repo)

        email_handler = SendPasswordResetEmailHandler(
            email_service=email_service,
            token_service=token_service,
        )

        service = SendPasswordResetEmailService(
            repo=repo, prepare_use_case=prepare_use_case, email_handler=email_handler
        )

        dto = PrepareSendForgotPasswordEmailInput(user_email=data.email)

        await service.execute(dto)

    except (UserNotFoundError, UserInactiveError):
        # retornamos 200 com uma msg generica para não dar info
        return {
            "message": "if user exists and is active a link was sent to reset password"
        }
    except EmailServiceUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="email_service_unavailable"
        )
    except EmailSentFailedError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="email_send_failed",
        )

    return {"message": "if user exists and is active a link was sent to reset password"}


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    current_password_context: PasswordContext = Depends(
        get_current_reset_password_context
    ),
    repo=Depends(get_users_repository),
):
    use_case = ResetPasswordUseCase(repo)
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

    return Response(status_code=201)
