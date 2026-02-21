from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.create_user_dto import CreateUserInput
from app.core.exceptions.users import UserAlreadyExistsError
from app.core.normalize.normalize_email import normalize_email
from app.domain.studio.users.entities.user import User
from app.domain.studio.users.events.activation_email_requested import (
    ActivationEmailRequested,
)


class CreateUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: CreateUserInput) -> ActivationEmailRequested:
        email = normalize_email(data.user_email)
        user_already_exists = self.repo.find_by_email(email)
        if user_already_exists:
            raise UserAlreadyExistsError()

        user = User.create_pending(email=email)
        self.repo.create(user)
        return ActivationEmailRequested(
            user_id=user.id, email=user.email, activation_token_version=0
        )
