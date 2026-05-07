from datetime import datetime, timezone

from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.user_status_dto import PromoteUserInput
from app.core.exceptions.users import UserNotFoundError
from app.core.types.audit_actor_type import AuditActorType


class PromoteUserToAdminUseCase:

    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: PromoteUserInput):
        with self.uow:
            user = self.uow.users.find_by_id(data.user_id)

            if not user:
                raise UserNotFoundError()

            changed = user.promote_to_admin()

            if changed:
                self.uow.users.update(user)

                log = AuditLogEntry(
                    entity_name="users",
                    entity_id=user.id,
                    action="promote user to admin",
                    actor_id=data.actor_id,
                    actor_type=AuditActorType.USER,
                    changes={
                        "is_admin": {
                            "from": False,
                            "to": True,
                        }
                    },
                    performed_at=datetime.now(timezone.utc),
                )

                self.uow.audit_logs.create(log)
