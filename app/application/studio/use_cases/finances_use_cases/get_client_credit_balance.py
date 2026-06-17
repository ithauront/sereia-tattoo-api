from uuid import UUID

from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.core.exceptions.users import VipClientNotFoundError


class GetClientCreditBalanceUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, vip_client_id: UUID) -> int:

        with self.uow:
            vip_client = self.uow.vip_clients.find_by_id(vip_client_id=vip_client_id)

            if not vip_client:
                raise VipClientNotFoundError()

            balance = self.uow.client_credit_entries.get_balance(vip_client_id=vip_client_id)

        return balance
