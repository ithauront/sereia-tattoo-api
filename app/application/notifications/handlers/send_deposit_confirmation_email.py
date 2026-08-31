from app.application.notifications.handlers.utils.render_confirm_deposit_client_email import (
    render_confirm_deposit_client_email,
)
from app.application.notifications.ports.email_service import EmailService
from app.domain.studio.finances.events.send_deposit_confirmation_email import (
    SendDepositConfirmationEmailEvent,
)


class SendDepositConfirmationEmailHandler:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: SendDepositConfirmationEmailEvent) -> None:

        client_html = render_confirm_deposit_client_email(
            amount=event.amount,
            appointment_type=event.appointment_type,
            start_at=event.start_at,
        )

        await self.email_service.send_email(
            to=event.client_email,
            subject="Parabéns, seu agendamento esta confirmado!",
            html_content=client_html,
        )
