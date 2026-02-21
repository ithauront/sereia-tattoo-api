from app.application.studio.repositories.vip_clients_repository import (
    VipClientsRepository,
)
from app.application.studio.use_cases.DTO.create_vip_client_dto import (
    CreateVipClientInput,
)
from app.core.exceptions.users import (
    ClientCodeAlreadyTakenError,
    EmailAlreadyTakenError,
    PhoneAlreadyTakenError,
)
from app.core.exceptions.validation import ValidationError
from app.core.normalize.normalize_phone import normalize_phone
from app.core.normalize.normalize_email import normalize_email
from app.core.validations.phone_number import validate_phone_number
from app.domain.studio.users.entities.value_objects.client_code import ClientCode
from app.domain.studio.users.entities.vip_client import VipClient
from app.domain.studio.users.events.create_vip_client_email_requested import (
    CreateVipClientEmailRequested,
)


# TODO: Fazer teste desse use_case inclusive se ele envia email sem persistir o usuario (não deveria)
class CreateVipClientUseCase:
    def __init__(self, repo: VipClientsRepository):
        self.repo = repo

    def execute(self, data: CreateVipClientInput) -> CreateVipClientEmailRequested:
        email = normalize_email(data.email)
        phone = normalize_phone(data.phone)
        email_exists = self.repo.find_by_email(email)
        try:
            validate_phone_number(phone)
        except ValidationError:
            raise
        phone_exists = self.repo.find_by_phone(phone)
        client_code_exists = self.repo.find_by_client_code(data.client_code)

        if email_exists:
            raise EmailAlreadyTakenError()
        if phone_exists:
            raise PhoneAlreadyTakenError()
        if client_code_exists:
            raise ClientCodeAlreadyTakenError()

        vip_client = VipClient.create(
            first_name=data.first_name,
            last_name=data.last_name,
            email=email,
            phone=phone,
            client_code=ClientCode(data.client_code),
        )
        self.repo.create(vip_client)
        return CreateVipClientEmailRequested(
            email=vip_client.email, client_code=str(vip_client.client_code)
        )
