from app.domain.notifications.handlers.send_user_activation_email import (
    SendUserActivationHandler,
)
from app.domain.users.events.activation_email_requested import ActivationEmailRequested
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.domain.users.use_cases.prepare_resend_activation_email import (
    PrepareResendActivationEmailUseCase,
)


class ResendActivationEmailService:
    def __init__(
        self,
        repo: UsersRepository,
        prepare_use_case: PrepareResendActivationEmailUseCase,
        email_handler: SendUserActivationHandler,
    ):
        self.repo = repo
        self.prepare_use_case = prepare_use_case
        self.email_handler = email_handler

    async def execute(self, data: PrepareResendActivationEmailInput) -> None:
        user = self.prepare_use_case.execute(data)

        event = ActivationEmailRequested(
            user_id=user.id,
            email=user.email,
            activation_token_version=user.activation_token_version + 1,
        )

        await self.email_handler.handle(event)

        user.bump_activation_token()
        self.repo.update(user)
