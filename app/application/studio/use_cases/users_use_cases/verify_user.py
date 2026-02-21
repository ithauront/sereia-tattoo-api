from uuid import UUID
from app.application.studio.repositories.users_repository import UsersRepository
from app.application.studio.use_cases.DTO.login_dto import VerifyInput, VerifyOutput
from app.core.exceptions.security import TokenError
from app.core.security.versioned_token_service import VersionedTokenService


class VerifyUserUseCase:
    def __init__(self, repo: UsersRepository, access_tokens: VersionedTokenService):
        self.repo = repo
        self.access_tokens = access_tokens

    def execute(self, data: VerifyInput) -> VerifyOutput:
        auth = data.authorization
        if not auth or not auth.lower().startswith("bearer "):
            raise TokenError("missing_bearer_token")

        token = auth.split(" ", 1)[1]

        try:
            payload = self.access_tokens.verify(token)
        except Exception:
            raise TokenError("invalid_token")

        try:
            user_id = UUID(payload["sub"])
        except Exception:
            raise TokenError("invalid_token")

        user = self.repo.find_by_id(user_id)
        if not user:
            raise TokenError("invalid_token")

        token_version = payload["ver"]
        if user.access_token_version != token_version:
            raise TokenError("token_revoked")

        return VerifyOutput(valid=True, sub=payload["sub"], type=payload["type"])
