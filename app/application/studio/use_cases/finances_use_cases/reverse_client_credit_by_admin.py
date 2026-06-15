from datetime import datetime, timezone

from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.audit_logs import AuditLogEntry
from app.application.studio.use_cases.DTO.reverse_client_credits import (
    ReverseClientCreditByAdminInput,
    ReverseClientCreditByAdminOutput,
)
from app.core.exceptions.marketing import (
    CannotReverseNegativeEntryError,
    CreditAlreadyReversedError,
    CreditEntryNotFoundError,
)
from app.core.exceptions.users import VipClientNotFoundError
from app.core.types.audit_actor_type import AuditActorType
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry


class ReverseClientCreditByAdminUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ReverseClientCreditByAdminInput) -> ReverseClientCreditByAdminOutput:
        with self.uow:
            vip_client = self.uow.vip_clients.find_by_id(data.vip_client_id)

            if not vip_client:
                raise VipClientNotFoundError()

            total_credits_before = self.uow.client_credit_entries.get_balance(
                vip_client_id=data.vip_client_id
            )

            credit_to_reverse = self.uow.client_credit_entries.find_by_id(credit_id=data.credit_id)

            if not credit_to_reverse:
                raise CreditEntryNotFoundError()

            if credit_to_reverse.is_debit:
                raise CannotReverseNegativeEntryError()

            existing_reversal = self.uow.client_credit_entries.find_by_related_entry(
                credit_to_reverse.id
            )

            if existing_reversal:
                raise CreditAlreadyReversedError()

            reversed_credit = ClientCreditEntry.reverse(
                vip_client_id=vip_client.id,
                admin_id=data.actor_id,
                original_entry_id=credit_to_reverse.id,
                quantity=credit_to_reverse.quantity,
                reason=data.reason,
            )

            self.uow.client_credit_entries.create(reversed_credit)

            total_credits_after = self.uow.client_credit_entries.get_balance(
                vip_client_id=data.vip_client_id
            )

            log = AuditLogEntry(
                entity_name="client_credit_entry",
                entity_id=reversed_credit.id,
                action="admin reverse credits",
                actor_id=data.actor_id,
                actor_type=AuditActorType.USER,
                changes={
                    "balance": {
                        "from": total_credits_before,
                        "to": total_credits_after,
                    },
                    "credit": {
                        "source_type": ClientCreditSourceType.REVERSED_BY_ADMIN,
                        "quantity": reversed_credit.quantity,
                        "original_credit": credit_to_reverse.id,
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

            return ReverseClientCreditByAdminOutput(
                before=total_credits_before,
                after=total_credits_after,
                reversed_credit_id=reversed_credit.id,
            )
