from app.core.exceptions.users import (
    InvalidPasswordTokenError,
    UserInactiveError,
    UserNotFoundError,
)
from app.core.security.passwords import hash_password
from app.core.validations.password import validate_password
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.password_dto import ResetPasswordInput


class ResetPasswordUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: ResetPasswordInput):
        user = self.repo.find_by_id(data.user_id)
        if not user:
            raise UserNotFoundError()
        if user.password_token_version != data.password_token_version:
            raise InvalidPasswordTokenError()
        if not user.is_active:
            raise UserInactiveError()

        validate_password(data.password)

        new_hashed_password = hash_password(data.password)
        user.change_password(new_hashed_password)

        self.repo.update(user)
