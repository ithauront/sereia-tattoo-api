from uuid import UUID
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.login_dto import RefreshInput, TokenOutput
from app.core.exceptions.security import TokenError
from app.core.exceptions.users import AuthenticationFailedError
from app.core.security.versioned_token_service import VersionedTokenService


class RefreshUserUseCase:
    def __init__(
        self,
        uow: ReadUnitOfWork,
        refresh_tokens: VersionedTokenService,
        access_tokens: VersionedTokenService,
    ):
        self.uow = uow
        self.refresh_tokens = refresh_tokens
        self.access_tokens = access_tokens

    def execute(self, data: RefreshInput) -> TokenOutput:

        try:
            payload = self.refresh_tokens.verify(data.refresh_token)
        except Exception:
            raise TokenError("invalid_token")

        try:
            user_id = UUID(payload["sub"])
        except Exception:
            raise TokenError("invalid_token")
        
        with self.uow:
            user = self.uow.users.find_by_id(user_id)

        if not user or not user.is_active:
            raise AuthenticationFailedError("user_not_found_or_inactive")

        try:
            token_version = payload["ver"]
        except Exception:
            raise TokenError("invalid_token")

        if user.refresh_token_version != token_version:
            raise TokenError("token_revoked")

        access = self.access_tokens.create(
            user_id=str(user.id), version=user.access_token_version
        )

        refresh = self.refresh_tokens.create(
            user_id=str(user.id), version=user.refresh_token_version
        )

        return TokenOutput(access_token=access, refresh_token=refresh)
