from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.create_user_dto import CreateUserInput
from app.core.exceptions.users import UserAlreadyExistsError
from app.core.normalize.normalize_email import normalize_email
from app.domain.studio.users.entities.user import User
from app.domain.studio.users.events.activation_email_requested import (
    ActivationEmailRequested,
)


class CreateUserUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: CreateUserInput) -> ActivationEmailRequested:
        email = normalize_email(data.user_email)

        with self.uow:
            user_already_exists = self.uow.users.find_by_email(email)
            if user_already_exists:
                raise UserAlreadyExistsError()

            user = User.create_pending(email=email)
            self.uow.users.create(user)

            event = user.request_activation_email()

            return event
