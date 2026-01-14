from app.core.exceptions.users import UserAlreadyExistsError
from app.domain.users.entities.user import User
from app.domain.users.events.activation_email_requested import (
    ActivationEmailRequested,
)
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.create_user_dto import CreateUserInput


class CreateUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: CreateUserInput) -> ActivationEmailRequested:
        user_already_exists = self.repo.find_by_email(data.user_email)
        if user_already_exists:
            raise UserAlreadyExistsError()

        user = User.create_pending(email=data.user_email)
        self.repo.create(user)
        return ActivationEmailRequested(
            user_id=user.id, email=user.email, activation_token_version=0
        )
