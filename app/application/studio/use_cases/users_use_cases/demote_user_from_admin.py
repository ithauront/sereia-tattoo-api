from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.user_status_dto import DemoteUserInput
from app.core.exceptions.users import (
    CannotDemoteYourselfError,
    LastAdminCannotBeDemotedError,
    UserNotFoundError,
)


class DemoteUserFromAdminUseCase:

    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: DemoteUserInput):
        with self.uow:
            user = self.uow.users.find_by_id(data.user_id)

            if not user:
                raise UserNotFoundError()

            if data.actor_id == user.id:
                raise CannotDemoteYourselfError()

            if user.is_admin and user.is_active:
                admins = self.uow.users.find_many(is_admin=True, is_active=True)
                if len(admins) == 1:
                    raise LastAdminCannotBeDemotedError()

            changed = user.demote_from_admin()

            if changed:
                self.uow.users.update(user)
