from app.core.exceptions.users import UserActivatedBeforeError, UserNotFoundError
from app.domain.users.entities.user import User
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)


class PrepareResendActivationEmailUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: PrepareResendActivationEmailInput) -> User:
        email = data.user_email.strip().lower()
        user = self.repo.find_by_email(email)

        if not user:
            raise UserNotFoundError()

        if user.has_activated_once:
            raise UserActivatedBeforeError()

        return user
