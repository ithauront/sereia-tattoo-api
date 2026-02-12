from app.core.exceptions.users import UserNotFoundError
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.login_dto import LogoutInput


class LogoutUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: LogoutInput):
        user = self.repo.find_by_id(data.user_id)
        if not user:
            raise UserNotFoundError()

        user.logout()

        self.repo.update(user)
