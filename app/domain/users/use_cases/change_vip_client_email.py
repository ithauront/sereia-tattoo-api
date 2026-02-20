from app.core.exceptions.users import EmailAlreadyTakenError, VipClientNotFoundError
from app.core.normalize.normalize_email import normalize_email
from app.domain.users.repositories.vip_clients_repository import VipClientsRepository
from app.domain.users.use_cases.DTO.change_email_dto import ChangeVipClientEmailInput


class ChangeVipClientEmailUseCase:
    def __init__(self, repo: VipClientsRepository):
        self.repo = repo

    def execute(self, data: ChangeVipClientEmailInput):
        vip_client = self.repo.find_by_id(data.vip_client_id)

        if not vip_client:
            raise VipClientNotFoundError()

        new_email = normalize_email(data.new_email)

        if vip_client.email == new_email:
            return

        if self.repo.find_by_email(new_email):
            raise EmailAlreadyTakenError()

        vip_client.change_email(new_email)

        self.repo.update(vip_client)
