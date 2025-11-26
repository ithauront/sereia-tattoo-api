from app.core.config import settings
from app.core.security import jwt_service
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.login_dto import RefreshInput, TokenOutput


# TODO fazer teste desse useCase
class RefreshUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: RefreshInput) -> TokenOutput:

        try:
            payload = jwt_service.verify(data.refresh_token, expected_type="refresh")
        except Exception:
            raise ValueError("invalid_token")

        user_id = payload["sub"]
        user = self.repo.find_by_id(user_id)

        if not user or not user.is_active:
            raise ValueError("user_not_found_or_inactive")

        access = jwt_service.create(
            subject=str(user.id),
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            token_type="access",
        )

        refresh = jwt_service.create(
            subject=str(user.id),
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
            token_type="refresh",
        )

        return TokenOutput(access_token=access, refresh_token=refresh)
