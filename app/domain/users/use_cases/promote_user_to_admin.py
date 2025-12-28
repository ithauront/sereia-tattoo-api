from app.domain.users.use_cases.DTO.user_status_dto import PromoteUserInput


class PromoteUserToAdminUseCase:

    def __init__(self, repo):
        self.repo = repo

    def execute(self, data: PromoteUserInput):
        user = self.repo.find_by_id(data.user_id)

        if not user:
            raise ValueError("user_not_found")

        changed = user.promote_to_admin()

        if changed:
            self.repo.update(user)
