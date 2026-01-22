from app.core.security.versioned_token_service import VersionedTokenService
from app.domain.notifications.handlers.utils.render_password_reset_email import (
    render_password_reset_email,
)

from app.domain.notifications.ports.email_service import EmailService
from app.domain.users.events.password_reset_email_requested import (
    PasswordResetEmailRequested,
)


# TODO: colocar o link correto quando o frontend estiver pronto.
class SendPasswordResetEmailHandler:
    def __init__(
        self, email_service: EmailService, token_service: VersionedTokenService
    ):
        self.email_service = email_service
        self.token_service = token_service

    async def handle(self, event: PasswordResetEmailRequested) -> None:

        token = self.token_service.create(
            str(event.user_id), version=event.password_token_version
        )
        reset_password_link = f"https://frontend/activate?token={token}"

        html = render_password_reset_email(reset_password_link)

        await self.email_service.send_email(
            to=event.email, subject="Recuperação de senha", html_content=html
        )
