from app.application.notifications.handlers.utils.render_vip_account_created_email import (
    render_vip_account_created_email,
)
from app.application.notifications.ports.email_service import EmailService
from app.domain.studio.users.events.create_vip_client_email_requested import (
    CreateVipClientEmailRequested,
)


# Fazer teste desse handler
class SendVipClientCreationNotificationEmailHandler:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: CreateVipClientEmailRequested) -> None:

        html = render_vip_account_created_email(event.client_code)

        await self.email_service.send_email(
            to=event.email,
            subject="Parabéns, você agora é um cliente VIP do Sereia Tattoo Studio",
            html_content=html,
        )
