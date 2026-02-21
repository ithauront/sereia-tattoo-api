from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.core.exceptions.users import UserActivatedBeforeError, UserNotFoundError
from app.core.normalize.normalize_email import normalize_email
from app.domain.studio.users.entities.user import User


class PrepareResendActivationEmailUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: PrepareResendActivationEmailInput) -> User:
        email = normalize_email(data.user_email)
        user = self.repo.find_by_email(email)

        if not user:
            raise UserNotFoundError()

        if user.has_activated_once:
            raise UserActivatedBeforeError()

        return user
