from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.core.exceptions.users import UserActivatedBeforeError, UserNotFoundError
from app.core.normalize.normalize_email import normalize_email
from app.domain.studio.users.entities.user import User


class PrepareResendActivationEmailUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: PrepareResendActivationEmailInput) -> User:
        email = normalize_email(data.user_email)
        with self.uow:
            user = self.uow.users.find_by_email(email)

        if not user:
            raise UserNotFoundError()

        if user.has_activated_once:
            raise UserActivatedBeforeError()

        return user
