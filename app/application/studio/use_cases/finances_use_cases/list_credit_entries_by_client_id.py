from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.list_client_credit_entries import (
    CreditEntryOutput,
    ListCreditEntriesByClientIdInput,
    ListCreditEntriesOutput,
)


class ListCreditEntriesByClientIdUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: ListCreditEntriesByClientIdInput):
        with self.uow:
            MAX_LIMIT = 100
            limit = min(data.limit, MAX_LIMIT)
            offset = (data.page - 1) * limit

            credits_entries = self.uow.client_credit_entries.find_many_by_vip_client_id(
                vip_client_id=data.vip_client_id,
                limit=limit,
                offset=offset,
                direction=data.direction,
            )

            total_entries = self.uow.client_credit_entries.count_by_vip_client_id(
                vip_client_id=data.vip_client_id
            )

        entries_output = [
            CreditEntryOutput.from_entity(entry) for entry in credits_entries
        ]

        return ListCreditEntriesOutput(
            entries=entries_output,
            total=total_entries,
            page=data.page,
            limit=limit,
        )
