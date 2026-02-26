from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.user_status_dto import ActivateUserInput
from app.core.exceptions.users import UserNotFoundError


class ActivateUserUseCase:

    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ActivateUserInput):
        with self.uow:
            user = self.uow.users.find_by_id(data.user_id)

            if not user:
                raise UserNotFoundError()

            changed = user.activate()

            if changed:
                self.uow.users.update(user)
