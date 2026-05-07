from datetime import datetime, timezone

from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.change_email_dto import (
    ChangeVipClientEmailInput,
)
from app.core.exceptions.users import EmailAlreadyTakenError, VipClientNotFoundError
from app.core.normalize.normalize_email import normalize_email
from app.core.types.audit_actor_type import AuditActorType


class ChangeVipClientEmailUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ChangeVipClientEmailInput):
        with self.uow:
            vip_client = self.uow.vip_clients.find_by_id(data.vip_client_id)

            if not vip_client:
                raise VipClientNotFoundError()

            old_email = vip_client.email

            new_email = normalize_email(data.new_email)

            if vip_client.email == new_email:
                return

            if self.uow.vip_clients.find_by_email(new_email):
                raise EmailAlreadyTakenError()

            vip_client.change_email(new_email)

            self.uow.vip_clients.update(vip_client)

            log = AuditLogEntry(
                entity_name="users",
                entity_id=vip_client.id,
                action="change vip client email",
                actor_id=data.actor_id,
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
