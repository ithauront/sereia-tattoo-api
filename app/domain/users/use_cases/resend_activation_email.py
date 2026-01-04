from app.domain.users.events.user_creation_requested import UserCreationRequested
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.create_user_dto import CreateUserInput


class ResendActivationEmailUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: CreateUserInput) -> UserCreationRequested:
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
