from app.domain.notifications.handlers.send_password_reset_email import (
    SendPasswordResetEmailHandler,
)

from app.domain.users.events.password_reset_email_requested import (
    PasswordResetEmailRequested,
)
from app.domain.users.repositories.users_repository import UsersRepository


from app.domain.users.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)
from app.domain.users.use_cases.prepare_send_forgot_password_email import (
    PrepareSendForgotPasswordEmailUseCase,
)


# TODO: avaliar se não devemos dar bump no token antes de enviar o email por conta de possivel inconsistencia de sistema externo e falsos positivos ou negativos que podem gerar bug
class SendPasswordResetEmailService:
    def __init__(
        self,
        repo: UsersRepository,
        prepare_use_case: PrepareSendForgotPasswordEmailUseCase,
        email_handler: SendPasswordResetEmailHandler,
    ):
        self.repo = repo
        self.prepare_use_case = prepare_use_case
        self.email_handler = email_handler

    async def execute(self, data: PrepareSendForgotPasswordEmailInput) -> None:
        user = self.prepare_use_case.execute(data)

        event = PasswordResetEmailRequested(
            user_id=user.id,
            email=user.email,
            password_token_version=user.password_token_version + 1,
        )

        await self.email_handler.handle(event)

        user.bump_password_token()
        user._touch()
        self.repo.update(user)
