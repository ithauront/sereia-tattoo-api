from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.core.exceptions.users import UserActivatedBeforeError, UserNotFoundError
from app.core.normalize.normalize_email import normalize_email
from app.domain.studio.users.events.activation_email_requested import (
    ActivationEmailRequested,
)


class PrepareResendActivationEmailUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(
        self, data: PrepareResendActivationEmailInput
    ) -> ActivationEmailRequested:
        with self.uow:
            email = normalize_email(data.user_email)

            user = self.uow.users.find_by_email(email)

            if not user:
                raise UserNotFoundError()

            if user.has_activated_once:
                raise UserActivatedBeforeError()

            event = user.request_activation_email()

            return event
