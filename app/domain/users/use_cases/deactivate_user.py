from app.core.exceptions.users import (
    CannotDeactivateYourselfError,
    LastAdminCannotBeDeactivatedError,
    UserNotFoundError,
)
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.user_status_dto import DeactivateUserInput


class DeactivateUserUseCase:

    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: DeactivateUserInput):
        user = self.repo.find_by_id(data.user_id)

        if not user:
            raise UserNotFoundError()

        if data.actor_id == user.id:
            raise CannotDeactivateYourselfError()

        if user.is_admin and user.is_active:
            admins = self.repo.find_many(is_admin=True, is_active=True)
            if len(admins) == 1:
                raise LastAdminCannotBeDeactivatedError()

        changed = user.deactivate()

        if changed:
            self.repo.update(user)
