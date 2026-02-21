from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.get_users_dto import (
    ListUsersInput,
    ListUsersOutput,
)
from app.application.studio.use_cases.DTO.user_output_dto import UserOutput


class ListUsersUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: ListUsersInput) -> ListUsersOutput:
        users = self.repo.find_many(is_active=data.is_active, is_admin=data.is_admin)

        admins = [user for user in users if user.is_admin]
        non_admins = [user for user in users if not user.is_admin]

        reverse = data.direction.lower() == "desc"

        if data.order_by == "username":
            admins.sort(key=lambda user: user.username.lower(), reverse=reverse)
            non_admins.sort(key=lambda user: user.username.lower(), reverse=reverse)
        elif data.order_by == "created_at":
            admins.sort(key=lambda user: user.created_at, reverse=reverse)
            non_admins.sort(key=lambda user: user.created_at, reverse=reverse)

        users = admins + non_admins

        start = (data.page - 1) * data.limit
        end = start + data.limit
        paginated = users[start:end]

        safe_users = [UserOutput.model_validate(user) for user in paginated]

        return ListUsersOutput(users=safe_users)
