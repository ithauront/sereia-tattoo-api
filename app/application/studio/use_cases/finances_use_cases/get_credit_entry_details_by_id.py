from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.get_client_credit_entries import (
    CreditEntryDetailsOutput,
    GetCreditEntryDetailsByIdInput,
)
from app.core.exceptions.marketing import CreditEntryNotFoundError
from app.core.exceptions.users import UserNotFoundError, VipClientNotFoundError
from app.domain.studio.finances.enums.client_credit_source_type import (
    ClientCreditSourceType,
)


class GetCreditEntryDetailsByIdUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: GetCreditEntryDetailsByIdInput) -> CreditEntryDetailsOutput:
        with self.uow:
            credit_entry = self.uow.client_credit_entries.find_by_id(
                credit_id=data.client_credit_id
            )
            if not credit_entry:
                raise CreditEntryNotFoundError()

            vip_client = self.uow.vip_clients.find_by_id(credit_entry.vip_client_id)
            if not vip_client:
                # Defensive check — Should never happen if data integrity is preserved
                raise VipClientNotFoundError()

            vip_client_name = " ".join(
                filter(None, [vip_client.first_name, vip_client.last_name])
            )

            admin_name = None

            if credit_entry.source_type in {
                ClientCreditSourceType.REVERSED_BY_ADMIN,
                ClientCreditSourceType.ADDED_BY_ADMIN,
            }:
                admin = self.uow.users.find_by_id(credit_entry.source_id)
                if not admin:
                    # Defensive check — Should never happen if data integrity is preserved
                    raise UserNotFoundError()

                admin_name = admin.username

            credit_entry_with_details = CreditEntryDetailsOutput.from_entity(
                vip_client_name=vip_client_name,
                credit_entry=credit_entry,
                admin_name=admin_name,
            )

            return credit_entry_with_details
