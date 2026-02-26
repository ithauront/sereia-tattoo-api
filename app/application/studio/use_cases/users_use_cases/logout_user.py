from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.login_dto import LogoutInput
from app.core.exceptions.users import UserNotFoundError


class LogoutUserUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: LogoutInput):
        with self.uow:
            user = self.uow.users.find_by_id(data.user_id)
            if not user:
                raise UserNotFoundError()

            user.logout()

            self.uow.users.update(user)
