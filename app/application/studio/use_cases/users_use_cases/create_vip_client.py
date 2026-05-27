from datetime import datetime, timezone

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.create_vip_client_dto import (
    CreateVipClientInput,
)
from app.core.exceptions.users import (
    ClientCodeAlreadyTakenError,
    EmailAlreadyTakenError,
    PhoneAlreadyTakenError,
)
from app.core.exceptions.validation import ValidationError
from app.core.normalize.normalize_phone import normalize_phone
from app.core.normalize.normalize_email import normalize_email
from app.core.types.audit_actor_type import AuditActorType
from app.core.validations.phone_number import validate_phone_number
from app.domain.studio.value_objects.client_code import ClientCode
from app.domain.studio.users.entities.vip_client import VipClient


class CreateVipClientUseCase:
    def __init__(self, uow: WriteUnitOfWork, integration_bus: IntegrationEventBus):
        self.uow = uow
        self.integration_bus = integration_bus

    async def execute(self, data: CreateVipClientInput) -> None:
        email = normalize_email(data.email)
        phone = normalize_phone(data.phone)

        with self.uow:
            email_exists = self.uow.vip_clients.find_by_email(email)
            if email_exists:
                raise EmailAlreadyTakenError()
            try:
                validate_phone_number(phone)
            except ValidationError:
                raise

            phone_exists = self.uow.vip_clients.find_by_phone(phone)
            if phone_exists:
                raise PhoneAlreadyTakenError()

            client_code_exists = self.uow.vip_clients.find_by_client_code(
                data.client_code
            )
            if client_code_exists:
                raise ClientCodeAlreadyTakenError()

            vip_client = VipClient.create(
                first_name=data.first_name,
                last_name=data.last_name,
                email=email,
                phone=phone,
                client_code=ClientCode(data.client_code),
            )
            self.uow.vip_clients.create(vip_client)

            log = AuditLogEntry(
                entity_name="users",
                entity_id=vip_client.id,
                action="create vip client",
                actor_id=data.actor_id,
                actor_type=AuditActorType.USER,
                changes={
                    "initial_state": {
                        "first_name": data.first_name,
                        "last_name": data.last_name,
                        "email": email,
                        "phone": phone,
                        "client_code": vip_client.client_code,
                    }
                },
                performed_at=datetime.now(timezone.utc),
            )

            self.uow.audit_logs.create(log)

            event = vip_client.create_vip_client_email_request()

        await self.integration_bus.publish(event)
