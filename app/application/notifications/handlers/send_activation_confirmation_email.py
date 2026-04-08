from app.application.notifications.handlers.utils.render_account_activated_email import (
    render_account_activated_email,
)

from app.application.notifications.ports.email_service import EmailService

from app.domain.studio.users.events.send_action_made_email_requested import (
    SendActionMadeEmailRequested,
)


class SendActivationConfirmationEmailHandler:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: SendActionMadeEmailRequested) -> None:

        html = render_account_activated_email()

        await self.email_service.send_email(
            to=event.email,
            subject="Parabéns, sua conta foi ativada!",
            html_content=html,
        )
