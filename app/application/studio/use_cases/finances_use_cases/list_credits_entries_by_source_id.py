from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.list_client_credit_entries import (
    CreditEntryOutput,
    ListCreditEntriesBySourceIdInput,
    ListCreditEntriesOutput,
)


# TODO: teste e teste de rota
class ListClientCreditEntriesBySourceIdUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: ListCreditEntriesBySourceIdInput) -> ListCreditEntriesOutput:
        with self.uow:
            MAX_LIMIT = 100
            limit = min(data.limit, MAX_LIMIT)
            offset = (data.page - 1) * limit

            credit_entries = self.uow.client_credit_entries.find_many_by_source_id(
                source_id=data.source_id, limit=limit, offset=offset, direction=data.direction
            )

            total_entries = self.uow.client_credit_entries.count_by_source_id(source_id=data.source_id)

        entries_output = [CreditEntryOutput.from_entity(entry) for entry in credit_entries]

        return ListCreditEntriesOutput(
            entries=entries_output, limit=limit, total=total_entries, page=data.page
        )
