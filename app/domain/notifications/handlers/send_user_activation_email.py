from app.core.security.versioned_token_service import VersionedTokenService
from app.domain.notifications.handlers.utils.render_activation_email import (
    render_activation_email,
)
from app.domain.notifications.ports.email_service import EmailService
from app.domain.users.events.activation_email_requested import ActivationEmailRequested


# TODO: colocar o link correto quando o frontend estiver pronto.
class SendUserActivationHandler:
    def __init__(
        self, email_service: EmailService, token_service: VersionedTokenService
    ):
        self.email_service = email_service
        self.token_service = token_service

    async def handle(self, event: ActivationEmailRequested) -> None:

        token = self.token_service.create(
            str(event.user_id), version=event.activation_token_version
        )
        activation_link = f"https://frontend/activate?token={token}"

        html = render_activation_email(activation_link)

        await self.email_service.send_email(
            to=event.email, subject="Ative sua conta", html_content=html
        )
