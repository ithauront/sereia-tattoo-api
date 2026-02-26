from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.change_email_dto import ChangeEmailInput
from app.core.exceptions.users import (
    AuthenticationFailedError,
    EmailAlreadyTakenError,
    UserNotFoundError,
)
from app.core.normalize.normalize_email import normalize_email
from app.core.security.passwords import verify_password


class ChangeEmailUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ChangeEmailInput):
        new_email = normalize_email(data.new_email)
        with self.uow:
            current_user = self.uow.users.find_by_id(data.user_id)
            if not current_user:
                raise UserNotFoundError()

            if new_email == current_user.email:
                return

            if not verify_password(data.password, current_user.hashed_password):
                raise AuthenticationFailedError()
            # mesmo que o usuario ja venha autenticado pelo token na rota
            # para esse tipo de operação acho interessante pediro o password novamente

            if self.uow.users.find_by_email(new_email):
                raise EmailAlreadyTakenError()

            current_user.change_email(new_email)

            self.uow.users.update(current_user)
