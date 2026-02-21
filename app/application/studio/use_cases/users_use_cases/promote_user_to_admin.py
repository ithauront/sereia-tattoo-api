from app.application.studio.use_cases.DTO.user_status_dto import PromoteUserInput
from app.core.exceptions.users import UserNotFoundError


class PromoteUserToAdminUseCase:

    def __init__(self, repo):
        self.repo = repo

    def execute(self, data: PromoteUserInput):
        user = self.repo.find_by_id(data.user_id)

        if not user:
            raise UserNotFoundError()

        changed = user.promote_to_admin()

        if changed:
            self.repo.update(user)
