from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.commun import Direction
from app.application.studio.use_cases.DTO.get_users_dto import (
    ListVipClientsInput,
    ListVipClientsOutput,
    VipClientsOrderBy,
)
from app.application.studio.use_cases.DTO.vip_client_output import VipClientOutput


class ListVipClientsUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: ListVipClientsInput) -> ListVipClientsOutput:
        with self.uow:
            vip_clients = self.uow.vip_clients.find_many()
        """
         Sorting and pagination are intentionally performed in memory.
         For the current expected dataset size (very small), this keeps the repository
         and queries simple without introducing unnecessary database complexity.

         If the dataset grows significantly in the future, this logic should be moved
         to the repository layer so that sorting and pagination are handled directly
         by the database (e.g., using ORDER BY, LIMIT, and OFFSET) to avoid loading
         large result sets into memory.
        """
        reverse = data.direction == Direction.desc

        if data.order_by == VipClientsOrderBy.first_name:
            vip_clients.sort(
                key=lambda vip_client: vip_client.first_name.lower(), reverse=reverse
            )
        elif data.order_by == VipClientsOrderBy.last_name:
            vip_clients.sort(
                key=lambda vip_client: vip_client.last_name.lower(), reverse=reverse
            )
        elif data.order_by == VipClientsOrderBy.created_at:
            vip_clients.sort(
                key=lambda vip_client: vip_client.created_at, reverse=reverse
            )
        elif data.order_by == VipClientsOrderBy.updated_at:
            vip_clients.sort(
                key=lambda vip_client: vip_client.updated_at, reverse=reverse
            )

        start = (data.page - 1) * data.limit
        end = start + data.limit
        paginated = vip_clients[start:end]

        safe_vip_clients = [
            VipClientOutput.from_entity(vip_client) for vip_client in paginated
        ]

        return ListVipClientsOutput(vip_clients=safe_vip_clients)
