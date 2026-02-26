from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.get_users_dto import GetUserInput
from app.application.studio.use_cases.DTO.user_output_dto import UserOutput
from app.core.exceptions.users import UserNotFoundError


class GetUserUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: GetUserInput) -> UserOutput:
        with self.uow:
            user = self.uow.users.find_by_id(data.user_id)

        if not user:
            raise UserNotFoundError()

        safe_user = UserOutput.model_validate(user)

        return safe_user
