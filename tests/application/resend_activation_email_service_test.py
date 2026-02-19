import pytest
from app.application.users.services.resend_activation_email_service import (
    ResendActivationEmailService,
)
from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
)
from app.domain.users.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.domain.users.use_cases.prepare_resend_activation_email import (
    PrepareResendActivationEmailUseCase,
)
from tests.fakes.fake_versioned_token import FakeVersionedTokenService
from tests.fakes.fake_email_service import FakeEmailService

from app.domain.notifications.handlers.send_user_activation_email import (
    SendUserActivationHandler,
)


async def test_resend_activation_email_service_success(users_repo, make_user):
    user = make_user(email="jhon@doe.com")
    users_repo.create(user)

    prepare_use_case = PrepareResendActivationEmailUseCase(users_repo)
    fake_email_service = FakeEmailService()
    fake_token_service = FakeVersionedTokenService()

    email_handler = SendUserActivationHandler(
        email_service=fake_email_service,
        token_service=fake_token_service,
    )

    service = ResendActivationEmailService(
        repo=users_repo,
        prepare_use_case=prepare_use_case,
        email_handler=email_handler,
    )
    dto = PrepareResendActivationEmailInput(user_email="jhon@doe.com")
    await service.execute(dto)

    assert fake_email_service.sent is True
    assert user.activation_token_version == 1


async def test_resend_activation_email_service_unavailable(users_repo, make_user):
    user = make_user(email="jhon@doe.com", activation_token_version=0)
    users_repo.create(user)

    prepare_use_case = PrepareResendActivationEmailUseCase(users_repo)
    fake_email_service = FakeEmailService(fail_with="email_service_unavailable")
    fake_token_service = FakeVersionedTokenService()

    email_handler = SendUserActivationHandler(
        email_service=fake_email_service,
        token_service=fake_token_service,
    )

    service = ResendActivationEmailService(
        repo=users_repo,
        prepare_use_case=prepare_use_case,
        email_handler=email_handler,
    )
    dto = PrepareResendActivationEmailInput(user_email="jhon@doe.com")
    with pytest.raises(EmailServiceUnavailableError):
        await service.execute(dto)

    assert user.activation_token_version == 0
    assert fake_email_service.sent is False


async def test_resend_activation_email_service_email_send_failed(users_repo, make_user):
    user = make_user(email="jhon@doe.com", activation_token_version=0)
    users_repo.create(user)

    prepare_use_case = PrepareResendActivationEmailUseCase(users_repo)

    fake_email_service = FakeEmailService(fail_with="email_send_failed")
    fake_token_service = FakeVersionedTokenService()

    email_handler = SendUserActivationHandler(
        email_service=fake_email_service,
        token_service=fake_token_service,
    )

    service = ResendActivationEmailService(
        repo=users_repo,
        prepare_use_case=prepare_use_case,
        email_handler=email_handler,
    )

    dto = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    with pytest.raises(EmailSentFailedError):
        await service.execute(dto)

    assert user.activation_token_version == 0
    assert fake_email_service.sent is False
