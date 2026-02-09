from app.core.exceptions.users import AuthenticationFailedError, EmailAlreadyTakenError
from app.core.security.passwords import verify_password
from app.domain.users.entities.user import User
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.change_email_dto import ChangeEmailInput


class ChangeEmailUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: ChangeEmailInput, current_user: User):
        new_email = data.new_email.strip().lower()

        if new_email == current_user.email:
            return

        if not verify_password(data.password, current_user.hashed_password):
            raise AuthenticationFailedError()
        # mesmo que o usuario ja venha autenticado pelo token na rota
        # para esse tipo de operação acho interessante pediro o password novamente

        if self.repo.find_by_email(new_email):
            raise EmailAlreadyTakenError()

        current_user.change_email(new_email)

        self.repo.update(current_user)
