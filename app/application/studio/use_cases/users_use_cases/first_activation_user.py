from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.first_activation_user_dto import (
    FirstActivationInput,
)
from app.core.exceptions.users import (
    InvalidActivationTokenError,
    UserActivatedBeforeError,
    UserNotFoundError,
    UsernameAlreadyTakenError,
)
from app.core.security.passwords import hash_password
from app.core.validations.password import validate_password
from app.core.validations.username import validate_username


# TODO: enviar um email para o usuario para confirmar para ele que a conta dele esta criada e ativa
class FirstActivationUserUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: FirstActivationInput):
        with self.uow:
            user = self.uow.users.find_by_id(data.user_id)
            if not user:
                raise UserNotFoundError()
            if user.has_activated_once:
                raise UserActivatedBeforeError()
            if user.activation_token_version != data.token_version:
                raise InvalidActivationTokenError()

            validate_username(data.username)
            username_already_in_db = self.uow.users.find_by_username(data.username)

            if username_already_in_db:
                raise UsernameAlreadyTakenError()

            validate_password(data.password)

            user.username = data.username
            user.hashed_password = hash_password(data.password)
            user.activate()

            self.uow.users.update(user)
