from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.password_dto import ResetPasswordInput
from app.core.exceptions.users import (
    InvalidPasswordTokenError,
    UserInactiveError,
    UserNotFoundError,
)
from app.core.security.passwords import hash_password
from app.core.validations.password import validate_password


class ResetPasswordUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ResetPasswordInput):
        with self.uow:
            user = self.uow.users.find_by_id(data.user_id)
            if not user:
                raise UserNotFoundError()
            if user.password_token_version != data.password_token_version:
                raise InvalidPasswordTokenError()
            if not user.is_active:
                raise UserInactiveError()

            validate_password(data.password)

            new_hashed_password = hash_password(data.password)
            user.change_password(new_hashed_password)

            self.uow.users.update(user)
