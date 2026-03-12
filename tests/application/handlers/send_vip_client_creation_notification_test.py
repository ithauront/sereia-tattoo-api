from app.application.notifications.handlers.send_vip_client_creation_notification_email import (
    SendVipClientCreationNotificationEmailHandler,
)
from app.domain.studio.users.events.create_vip_client_email_requested import (
    CreateVipClientEmailRequested,
)
from tests.fakes.fake_email_service import FakeEmailService


async def test_send_vip_client_creation_handler_sends_email():
    event = CreateVipClientEmailRequested(email="jhon@doe.com", client_code="JHON-AZUL")

    email_service = FakeEmailService()

    handler = SendVipClientCreationNotificationEmailHandler(email_service=email_service)

    await handler.handle(event)

    assert email_service.sent is True
    assert email_service.last_payload["to"] == "jhon@doe.com"
    assert (
        email_service.last_payload["subject"]
        == "Parabéns, você agora é um cliente VIP do Sereia Tattoo Studio"
    )
    assert "JHON-AZUL" in email_service.last_payload["html"]
