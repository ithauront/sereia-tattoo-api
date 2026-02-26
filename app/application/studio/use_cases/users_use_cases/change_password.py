from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.password_dto import ChangePasswordInput
from app.core.exceptions.users import AuthenticationFailedError, UserNotFoundError
from app.core.security.passwords import hash_password, verify_password
from app.core.validations.password import validate_password


class ChangePasswordUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ChangePasswordInput) -> None:
        with self.uow:
            current_user = self.uow.users.find_by_id(data.user_id)
            if not current_user:
                raise UserNotFoundError()

            if not verify_password(data.old_password, current_user.hashed_password):
                raise AuthenticationFailedError()

            validate_password(data.new_password)

            hashed_password = hash_password(data.new_password)

            current_user.change_password(hashed_password)

            self.uow.users.update(current_user)
