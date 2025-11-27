from app.core.security import jwt_service
from app.domain.users.repositories.users_repository import UsersRepository
from app.domain.users.use_cases.DTO.login_dto import VerifyInput, VerifyOutput


class VerifyUserUseCase:
    def __init__(self, repo: UsersRepository):
        self.repo = repo

    def execute(self, data: VerifyInput) -> VerifyOutput:
        auth = data.authorization
        if not auth or not auth.lower().startswith(
            "Bearer "
        ):
            raise ValueError("missing_bearer_token")

        token = auth.split(" ", 1)[1]

        try:
            payload = jwt_service.verify(token, expected_type="access")
        except Exception:
            raise ValueError("invalid_token")

        return VerifyOutput(valid=True, sub=payload["sub"], type=payload["type"])
