import pytest
from app.application.notifications.handlers.send_password_reset_email import (
    SendPasswordResetEmailHandler,
)
from app.application.studio.services.send_password_reset_email_service import (
    SendPasswordResetEmailService,
)
from app.application.studio.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)
from app.application.studio.use_cases.users_use_cases.prepare_send_forgot_password_email import (
    PrepareSendForgotPasswordEmailUseCase,
)
from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
)
from tests.fakes.fake_versioned_token import FakeVersionedTokenService
from tests.fakes.fake_email_service import FakeEmailService


async def test_send_password_reset_email_service_success(users_repo, make_user):
    user = make_user(email="jhon@doe.com", password_token_version=0)
    users_repo.create(user)

    prepare_use_case = PrepareSendForgotPasswordEmailUseCase(users_repo)
    fake_email_service = FakeEmailService()
    fake_token_service = FakeVersionedTokenService()

    email_handler = SendPasswordResetEmailHandler(
        email_service=fake_email_service,
        token_service=fake_token_service,
    )

    service = SendPasswordResetEmailService(
        repo=users_repo,
        prepare_use_case=prepare_use_case,
        email_handler=email_handler,
    )
    dto = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")
    await service.execute(dto)

    assert fake_email_service.sent is True
    assert user.password_token_version == 1


async def test_send_password_reset_email_service_unavailable(users_repo, make_user):
    user = make_user(email="jhon@doe.com", password_token_version=0)
    users_repo.create(user)

    prepare_use_case = PrepareSendForgotPasswordEmailUseCase(users_repo)
    fake_email_service = FakeEmailService(fail_with="email_service_unavailable")
    fake_token_service = FakeVersionedTokenService()

    email_handler = SendPasswordResetEmailHandler(
        email_service=fake_email_service,
        token_service=fake_token_service,
    )

    service = SendPasswordResetEmailService(
        repo=users_repo,
        prepare_use_case=prepare_use_case,
        email_handler=email_handler,
    )
    dto = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")
    with pytest.raises(EmailServiceUnavailableError):
        await service.execute(dto)

    assert user.password_token_version == 0
    assert fake_email_service.sent is False


async def test_send_password_reset_email_service_email_send_failed(
    users_repo, make_user
):
    user = make_user(email="jhon@doe.com", password_token_version=0)
    users_repo.create(user)

    prepare_use_case = PrepareSendForgotPasswordEmailUseCase(users_repo)

    fake_email_service = FakeEmailService(fail_with="email_send_failed")
    fake_token_service = FakeVersionedTokenService()

    email_handler = SendPasswordResetEmailHandler(
        email_service=fake_email_service,
        token_service=fake_token_service,
    )

    service = SendPasswordResetEmailService(
        repo=users_repo,
        prepare_use_case=prepare_use_case,
        email_handler=email_handler,
    )
    dto = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    with pytest.raises(EmailSentFailedError):
        await service.execute(dto)

    assert user.password_token_version == 0
    assert fake_email_service.sent is False
