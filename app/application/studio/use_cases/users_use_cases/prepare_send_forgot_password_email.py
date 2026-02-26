from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)
from app.core.exceptions.users import UserInactiveError, UserNotFoundError
from app.core.normalize.normalize_email import normalize_email


class PrepareSendForgotPasswordEmailUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: PrepareSendForgotPasswordEmailInput):
        email = normalize_email(data.user_email)
        with self.uow:
            user = self.uow.users.find_by_email(email)

        if not user:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserInactiveError()

        return user
