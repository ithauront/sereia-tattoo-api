from datetime import datetime, timezone

from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.add_client_credits import (
    AddClientCreditByAdminInput,
    AddClientCreditByAdminOutput,
)
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.core.exceptions.users import VipClientNotFoundError
from app.core.types.audit_actor_type import AuditActorType
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry


class AddClientCreditByAdminUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(
        self, data: AddClientCreditByAdminInput
    ) -> AddClientCreditByAdminOutput:
        with self.uow:
            vip_client = self.uow.vip_clients.find_by_id(data.vip_client_id)

            if not vip_client:
                raise VipClientNotFoundError()

            total_credits_before = self.uow.client_credit_entries.get_balance(
                vip_client_id=vip_client.id
            )

            client_credit = ClientCreditEntry.added_by_admin(
                vip_client_id=vip_client.id,
                admin_id=data.actor_id,
                quantity=data.quantity,
                reason=data.reason,
            )

            self.uow.client_credit_entries.create(client_credit_entry=client_credit)

            total_credits_after = self.uow.client_credit_entries.get_balance(
                vip_client_id=vip_client.id
            )

            log = AuditLogEntry(
                entity_name="client_credit_entry",
                entity_id=client_credit.id,
                action="admin added credits",
                actor_id=data.actor_id,
                actor_type=AuditActorType.USER,
                changes={
                    "balance": {
                        "from": total_credits_before,
                        "to": total_credits_after,
                    },
                    "credit": {
                        "source_type": ClientCreditSourceType.ADDED_BY_ADMIN,
                        "quantity": data.quantity,
                    },
                    "vip_client": {
                        "id": vip_client.id,
                        "client_code": vip_client.client_code,
                    },
                },
                reason=data.reason,
                performed_at=datetime.now(timezone.utc),
            )

            self.uow.audit_logs.create(log)

            return AddClientCreditByAdminOutput(
                before=total_credits_before, after=total_credits_after
            )
