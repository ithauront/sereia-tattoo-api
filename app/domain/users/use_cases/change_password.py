from app.core.security.passwords import hash_password, verify_password
from app.domain.users.entities.user import User
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.password_dto import ChangePasswordInput


class ChangePasswordUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: ChangePasswordInput, current_user: User) -> None:

        if not verify_password(data.old_password, current_user.hashed_password):
            raise ValueError("invalid_credentials")

        hashed_password = hash_password(data.new_password)

        current_user.change_password(hashed_password)

        self.repo.update(current_user)
