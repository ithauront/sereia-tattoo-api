from app.core.exceptions.users import UserInactiveError, UserNotFoundError
from app.core.normalize.normalize_email import normalize_email
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)


class PrepareSendForgotPasswordEmailUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: PrepareSendForgotPasswordEmailInput):
        email = normalize_email(data.user_email)
        user = self.repo.find_by_email(email)

        if not user:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserInactiveError()

        return user
