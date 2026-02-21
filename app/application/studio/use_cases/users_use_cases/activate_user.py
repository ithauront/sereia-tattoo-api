from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.user_status_dto import ActivateUserInput
from app.core.exceptions.users import UserNotFoundError


class ActivateUserUseCase:

    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: ActivateUserInput):
        user = self.repo.find_by_id(data.user_id)

        if not user:
            raise UserNotFoundError()

        changed = user.activate()

        if changed:
            self.repo.update(user)
