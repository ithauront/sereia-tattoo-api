from app.domain.users.entities.user import User
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)


class PrepareResendActivationEmailUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: PrepareResendActivationEmailInput) -> User:
        user = self.repo.find_by_email(data.user_email)

        if not user:
            raise ValueError("user_not_found")

        if user.has_activated_once:
            raise ValueError("user_has_been_activated_before")

        return user
