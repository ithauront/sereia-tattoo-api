from datetime import datetime, timezone

from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.change_email_dto import ChangeEmailInput
from app.core.exceptions.users import (
    AuthenticationFailedError,
    EmailAlreadyTakenError,
    UserNotFoundError,
)
from app.core.normalize.normalize_email import normalize_email
from app.core.security.passwords import verify_password
from app.core.types.audit_actor_type import AuditActorType


class ChangeEmailUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ChangeEmailInput):
        new_email = normalize_email(data.new_email)
        with self.uow:
            current_user = self.uow.users.find_by_id(data.user_id)
            if not current_user:
                raise UserNotFoundError()

            old_email = current_user.email

            if new_email == current_user.email:
                return

            if not verify_password(data.password, current_user.hashed_password):
                raise AuthenticationFailedError()
                """
                Even though the user is already authenticated via the token,
                we require the password again for this type of sensitive operation.
                """
            if self.uow.users.find_by_email(new_email):
                raise EmailAlreadyTakenError()

            current_user.change_email(new_email)

            self.uow.users.update(current_user)

            log = AuditLogEntry(
                entity_name="users",
                entity_id=current_user.id,
                action="change user email",
                actor_id=current_user.id,
                actor_type=AuditActorType.USER,
                changes={
                    "email": {
                        "from": old_email,
                        "to": new_email,
                    }
                },
                performed_at=datetime.now(timezone.utc),
            )

            self.uow.audit_logs.create(log)
