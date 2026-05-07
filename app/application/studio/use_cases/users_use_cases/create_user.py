from datetime import datetime, timezone

from app.application.event_bus.event_bus import EventBus
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.create_user_dto import CreateUserInput
from app.core.exceptions.users import UserAlreadyExistsError
from app.core.normalize.normalize_email import normalize_email
from app.core.types.audit_actor_type import AuditActorType
from app.domain.studio.users.entities.user import User


class CreateUserUseCase:
    def __init__(self, uow: WriteUnitOfWork, event_bus: EventBus):
        self.uow = uow
        self.event_bus = event_bus

    async def execute(self, data: CreateUserInput) -> None:
        email = normalize_email(data.user_email)

        with self.uow:
            user_already_exists = self.uow.users.find_by_email(email)
            if user_already_exists:
                raise UserAlreadyExistsError()

            user = User.create_pending(email=email)
            self.uow.users.create(user)

            event = user.request_activation_email()

            log = AuditLogEntry(
                entity_name="users",
                entity_id=user.id,
                action="create user",
                actor_id=data.actor_id,
                actor_type=AuditActorType.USER,
                changes={
                    "initial_state": {
                        "email": user.email,
                        "is_admin": user.is_admin,
                        "is_active": user.is_active,
                    }
                },
                performed_at=datetime.now(timezone.utc),
            )

            self.uow.audit_logs.create(log)

        await self.event_bus.publish(event)
