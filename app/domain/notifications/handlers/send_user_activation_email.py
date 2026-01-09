from app.core.security.activation_token_service import ActivationTokenService
from app.domain.notifications.handlers.utils.render_activation_email import (
    render_activation_email,
)
from app.domain.notifications.ports.email_service import EmailService
from app.domain.users.events.user_creation_requested import UserCreationRequested


# TODO: fazer teste desse handler
# TODO: colocar o link correto quando o frontend estiver pronto.
# TODO: para teste talvez apenas ir passando o token para frente até ele chegar na resposta da rota.
class SendUserActivationHandler:
    def __init__(
        self, email_service: EmailService, token_service: ActivationTokenService
    ):
        self.email_service = email_service
        self.token_service = token_service

    async def handle(self, event: UserCreationRequested) -> None:

        token = self.token_service.create(
            str(event.user_id), version=event.activation_token_version
        )
        activation_link = f"https://frontend/activate?token={token}"

        html = render_activation_email(activation_link)

        await self.email_service.send_email(
            to=event.email, subject="Ative sua conta", html_content=html
        )
