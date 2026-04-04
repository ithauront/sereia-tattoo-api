from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.application.studio.use_cases.DTO.get_users_dto import GetVipClientInput
from app.application.studio.use_cases.DTO.vip_client_output import (
    VipClientOutput,
    VipClientOutputWithDetails,
)
from app.core.exceptions.users import VipClientNotFoundError


class GetVipClientUseCase:
    def __init__(self, uow: ReadUnitOfWork):
        self.uow = uow

    def execute(self, data: GetVipClientInput) -> VipClientOutputWithDetails:
        with self.uow:
            vip_client = self.uow.vip_clients.find_by_id(data.vip_client_id)

            if not vip_client:
                raise VipClientNotFoundError()

            vip_client_credits_balance = self.uow.client_credit_entries.get_balance(
                vip_client_id=data.vip_client_id
            )

            safe_vip_client = VipClientOutput.from_entity(vip_client)

        return VipClientOutputWithDetails(
            vip_client=safe_vip_client, balance=vip_client_credits_balance
        )
