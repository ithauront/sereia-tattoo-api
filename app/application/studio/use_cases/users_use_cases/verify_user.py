from uuid import UUID
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.login_dto import VerifyInput, VerifyOutput
from app.application.studio.use_cases.DTO.user_output_dto import UserVerifyDTO
from app.core.exceptions.security import TokenError
from app.core.security.versioned_token_service import VersionedTokenService


class VerifyUserUseCase:
    def __init__(self, uow: ReadUnitOfWork, access_tokens: VersionedTokenService):
        self.uow = uow
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

        user = self.uow.users.find_by_id(user_id)
        if not user:
            raise TokenError("invalid_token")

        token_version = payload["ver"]
        if user.access_token_version != token_version:
            raise TokenError("token_revoked")

        user_verified = UserVerifyDTO(
            id=user.id,
            is_active=user.is_active,
            is_admin=user.is_admin,
        )

        return VerifyOutput(
            valid=True, sub=payload["sub"], type=payload["type"], user=user_verified
        )
