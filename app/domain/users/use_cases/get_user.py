from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.get_users_dto import GetUserInput
from app.domain.users.use_cases.DTO.user_output_dto import UserOutput


class GetUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: GetUserInput) -> UserOutput:
        user = self.repo.find_by_id(data.user_id)

        if not user:
            raise ValueError("user_not_found")

        safe_user = UserOutput.model_validate(user)

        return safe_user
