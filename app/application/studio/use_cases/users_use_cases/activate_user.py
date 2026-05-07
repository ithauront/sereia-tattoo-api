from datetime import datetime, timezone

from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.user_status_dto import ActivateUserInput
from app.core.exceptions.users import UserNotFoundError
from app.core.types.audit_actor_type import AuditActorType


class ActivateUserUseCase:

    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ActivateUserInput):
        with self.uow:
            user = self.uow.users.find_by_id(data.user_id)

            if not user:
                raise UserNotFoundError()

            changed = user.activate()

            if changed:
                self.uow.users.update(user)

                log = AuditLogEntry(
                    entity_name="users",
                    entity_id=user.id,
                    action="activate user",
                    actor_id=data.actor_id,
                    actor_type=AuditActorType.USER,
                    changes={
                        "is_active": {
                            "from": False,
                            "to": True,
                        }
                    },
                    performed_at=datetime.now(timezone.utc),
                )

                self.uow.audit_logs.create(log)
