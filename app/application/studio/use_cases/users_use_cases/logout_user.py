from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.login_dto import LogoutInput
from app.core.exceptions.users import UserNotFoundError


class LogoutUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: LogoutInput):
        user = self.repo.find_by_id(data.user_id)
        if not user:
            raise UserNotFoundError()

        user.logout()

        self.repo.update(user)
