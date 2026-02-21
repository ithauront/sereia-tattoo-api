from uuid import uuid4
from app.application.notifications.handlers.send_user_activation_email import (
    SendUserActivationHandler,
)
from app.domain.studio.users.events.activation_email_requested import (
    ActivationEmailRequested,
)
from tests.fakes.fake_versioned_token import FakeVersionedTokenService
from tests.fakes.fake_email_service import FakeEmailService


async def test_send_user_activation_handler_sends_email():
    user_id = uuid4()
    event = ActivationEmailRequested(
        user_id=user_id, email="jhon@doe.com", activation_token_version=1
    )

    email_service = FakeEmailService()
    token_service = FakeVersionedTokenService()

    handler = SendUserActivationHandler(
        email_service=email_service, token_service=token_service
    )

    await handler.handle(event)

    assert email_service.sent is True
    assert email_service.last_payload["to"] == "jhon@doe.com"
    assert email_service.last_payload["subject"] == "Ative sua conta"
    assert "fake-token" in email_service.last_payload["html"]
