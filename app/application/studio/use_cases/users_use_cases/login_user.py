from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.login_dto import LoginInput, TokenOutput
from app.core.exceptions.users import AuthenticationFailedError, UserInactiveError
from app.core.normalize.normalize_email import normalize_email
from app.core.security.passwords import verify_password
from app.core.security.versioned_token_service import VersionedTokenService


class LoginUserUseCase:
    def __init__(
        self,
        repo: UsersRepository,
        access_tokens: VersionedTokenService,
        refresh_tokens: VersionedTokenService,
    ):
        self.repo = repo
        self.access_tokens = access_tokens
        self.refresh_tokens = refresh_tokens

    def execute(self, data: LoginInput) -> TokenOutput:
        if "@" in data.identifier:
            email = normalize_email(data.identifier)
            user = self.repo.find_by_email(email)
        else:
            user = self.repo.find_by_username(data.identifier)

        if not user:
            raise AuthenticationFailedError()

        if user.is_active is False:
            raise UserInactiveError()

        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationFailedError()

        access_version = user.access_token_version
        refresh_version = user.refresh_token_version

        access_token = self.access_tokens.create(
            user_id=str(user.id), version=access_version
        )

        refresh_token = self.refresh_tokens.create(
            user_id=str(user.id), version=refresh_version
        )

        return TokenOutput(access_token=access_token, refresh_token=refresh_token)
