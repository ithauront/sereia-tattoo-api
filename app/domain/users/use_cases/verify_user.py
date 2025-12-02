from uuid import UUID
from app.core.security import jwt_service
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.login_dto import VerifyInput, VerifyOutput


class VerifyUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: VerifyInput) -> VerifyOutput:
        auth = data.authorization
        if not auth or not auth.lower().startswith("bearer "):
            raise ValueError("missing_bearer_token")

        token = auth.split(" ", 1)[1]

        try:
            payload = jwt_service.verify(token, expected_type="access")
        except Exception:
            raise ValueError("invalid_token")

        try:
            user_id = UUID(payload["sub"])
        except Exception:
            raise ValueError("invalid_token")

        user = self.repo.find_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("invalid_token")

        return VerifyOutput(valid=True, sub=payload["sub"], type=payload["type"])
