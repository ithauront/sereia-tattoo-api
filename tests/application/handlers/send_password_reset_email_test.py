from uuid import uuid4

from app.application.notifications.handlers.send_password_reset_email import (
    SendPasswordResetEmailHandler,
)
from app.domain.studio.users.events.password_reset_email_requested import (
    PasswordResetEmailRequested,
)
from tests.fakes.fake_versioned_token import FakeVersionedTokenService
from tests.fakes.fake_email_service import FakeEmailService


async def test_send_password_reset_handler_sends_email():
    user_id = uuid4()
    event = PasswordResetEmailRequested(
        user_id=user_id, email="jhon@doe.com", password_token_version=1
    )

    email_service = FakeEmailService()
    token_service = FakeVersionedTokenService()

    handler = SendPasswordResetEmailHandler(
        email_service=email_service, token_service=token_service
    )

    await handler.handle(event)

    assert email_service.sent is True
    assert email_service.last_payload["to"] == "jhon@doe.com"
    assert email_service.last_payload["subject"] == "Recuperação de senha"
    assert "fake-token" in email_service.last_payload["html"]
