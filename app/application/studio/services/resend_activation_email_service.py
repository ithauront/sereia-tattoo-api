from app.application.notifications.handlers.send_user_activation_email import (
    SendUserActivationHandler,
)
from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.application.studio.use_cases.users_use_cases.prepare_resend_activation_email import (
    PrepareResendActivationEmailUseCase,
)
from app.domain.studio.users.events.activation_email_requested import (
    ActivationEmailRequested,
)


# TODO:
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

        user._touch()
        self.repo.update(user)

        await self.email_handler.handle(event)

        user.bump_activation_token()
