from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.change_email_dto import (
    ChangeVipClientEmailInput,
)
from app.core.exceptions.users import EmailAlreadyTakenError, VipClientNotFoundError
from app.core.normalize.normalize_email import normalize_email


class ChangeVipClientEmailUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ChangeVipClientEmailInput):
        with self.uow:
            vip_client = self.uow.vip_clients.find_by_id(data.vip_client_id)

            if not vip_client:
                raise VipClientNotFoundError()

            new_email = normalize_email(data.new_email)

            if vip_client.email == new_email:
                return

            if self.uow.vip_clients.find_by_email(new_email):
                raise EmailAlreadyTakenError()

            vip_client.change_email(new_email)

            self.uow.vip_clients.update(vip_client)
