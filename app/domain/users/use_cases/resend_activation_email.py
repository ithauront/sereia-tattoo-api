from app.domain.users.events.user_creation_requested import UserCreationRequested
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.resend_activation_email_dto import (
    ResendActivationEmailInput,
)


class ResendActivationEmailUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: ResendActivationEmailInput) -> UserCreationRequested:
        user = self.repo.find_by_email(data.user_email)
        if not user:
            raise ValueError("user_not_found")
        if user.has_activated_once:
            raise ValueError("user_has_been_activated_before")

        user.bump_activation_token()
        self.repo.update(user)

        return UserCreationRequested(
            user_id=user.id,
            email=user.email,
            activation_token_version=user.activation_token_version,
        )
