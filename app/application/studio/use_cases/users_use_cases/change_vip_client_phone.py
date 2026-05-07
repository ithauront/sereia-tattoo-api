from datetime import datetime, timezone

from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.change_phone_dto import (
    ChangeVipClientPhoneInput,
)
from app.core.exceptions.users import PhoneAlreadyTakenError, VipClientNotFoundError
from app.core.normalize.normalize_phone import normalize_phone
from app.core.types.audit_actor_type import AuditActorType
from app.core.validations.phone_number import validate_phone_number


class ChangeVipClientPhoneUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ChangeVipClientPhoneInput):
        with self.uow:
            vip_client = self.uow.vip_clients.find_by_id(data.vip_client_id)

            if not vip_client:
                raise VipClientNotFoundError()

            old_phone = vip_client.phone

            new_phone = normalize_phone(data.new_phone)
            validate_phone_number(new_phone)

            if vip_client.phone == new_phone:
                return

            if self.uow.vip_clients.find_by_phone(new_phone):
                raise PhoneAlreadyTakenError()

            vip_client.change_phone(new_phone)

            self.uow.vip_clients.update(vip_client)

            log = AuditLogEntry(
                entity_name="users",
                entity_id=vip_client.id,
                action="change vip client phone",
                actor_id=data.actor_id,
                actor_type=AuditActorType.USER,
                changes={
                    "phone": {
                        "from": old_phone,
                        "to": new_phone,
                    }
                },
                performed_at=datetime.now(timezone.utc),
            )

            self.uow.audit_logs.create(log)
