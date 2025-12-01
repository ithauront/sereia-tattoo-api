from app.core.security import jwt_service
from app.core.security.passwords import verify_password
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.login_dto import LoginInput, TokenOutput
from app.core.config import settings


class LoginUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: LoginInput) -> TokenOutput:
        if "@" in data.identifier:
            user = self.repo.find_by_email(data.identifier)
        else:
            user = self.repo.find_by_username(data.identifier)

        if not user:
            raise ValueError("invalid_credentials")

        if not verify_password(data.password, user.hashed_password):
            raise ValueError("invalid_credentials")

        access_token = jwt_service.create(
            subject=str(user.id),
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            token_type="access",
        )

        refresh_token = jwt_service.create(
            subject=str(user.id),
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
            token_type="refresh",
        )

        return TokenOutput(access_token=access_token, refresh_token=refresh_token)
