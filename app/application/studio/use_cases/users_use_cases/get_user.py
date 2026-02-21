from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.get_users_dto import GetUserInput
from app.application.studio.use_cases.DTO.user_output_dto import UserOutput
from app.core.exceptions.users import UserNotFoundError


class GetUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: GetUserInput) -> UserOutput:
        user = self.repo.find_by_id(data.user_id)

        if not user:
            raise UserNotFoundError()

        safe_user = UserOutput.model_validate(user)

        return safe_user
