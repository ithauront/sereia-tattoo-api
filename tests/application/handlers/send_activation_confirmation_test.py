from app.application.notifications.handlers.send_activation_confirmation_email import (
    SendActivationConfirmationEmailHandler,
)
from app.domain.studio.users.events.send_action_made_email_requested import (
    SendActionMadeEmailRequested,
)
from tests.fakes.fake_email_service import FakeEmailService


async def test_send_activation_confirmation_handler_sends_email():
    event = SendActionMadeEmailRequested(email="jhon@doe.com")

    email_service = FakeEmailService()

    handler = SendActivationConfirmationEmailHandler(email_service=email_service)

    await handler.handle(event)

    assert email_service.sent is True
    assert email_service.last_payload["to"] == "jhon@doe.com"
    assert email_service.last_payload["subject"] == "Parabéns, sua conta foi ativada!"
    assert (
        "Agora você já pode utilizar nossos serviços e gerenciar sua conta normalmente."
        in email_service.last_payload["html"]
    )
