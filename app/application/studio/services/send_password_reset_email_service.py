from app.application.notifications.handlers.send_password_reset_email import (
    SendPasswordResetEmailHandler,
)
from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)
from app.application.studio.use_cases.users_use_cases.prepare_send_forgot_password_email import (
    PrepareSendForgotPasswordEmailUseCase,
)
from app.domain.studio.users.events.password_reset_email_requested import (
    PasswordResetEmailRequested,
)


# NOTE:
# Currently, we bump the token version *after* sending the email to avoid
# inconsistencies when external services fail (no transactional boundary yet).
#
# Once a Unit of Work with transactional commit + event dispatching is implemented,
# this should be inverted:
#   1) bump token version
#   2) commit domain state
#   3) publish ActivationEmailRequested event AFTER COMMIT (outbox pattern)
#
# This will guarantee domain consistency even if the email service is unavailable.
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
