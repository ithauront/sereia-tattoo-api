from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.user_status_dto import DemoteUserInput


class DemoteUserFromAdminUseCase:

    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: DemoteUserInput):
        user = self.repo.find_by_id(data.user_id)

        if not user:
            raise ValueError("user_not_found")

        if data.actor_id == user.id:
            raise ValueError("cannot_demote_yourself")

        if user.is_admin and user.is_active:
            admins = self.repo.find_many(is_admin=True, is_active=True)
            if len(admins) == 1:
                raise ValueError("last_admin_cannot_be_demoted")

        changed = user.demote_from_admin()

        if changed:
            self.repo.update(user)
