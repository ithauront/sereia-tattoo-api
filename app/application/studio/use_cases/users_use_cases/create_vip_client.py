from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
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


# TODO: testar esse use_case inclusive que ele não deve envia email sem persistir o user
# acho que o email vai ser testado em um teste de integração porque é efeito coleteral
class CreateVipClientUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: CreateVipClientInput) -> CreateVipClientEmailRequested:
        email = normalize_email(data.email)
        phone = normalize_phone(data.phone)

        with self.uow:
            email_exists = self.uow.vip_clients.find_by_email(email)
            if email_exists:
                raise EmailAlreadyTakenError()
            try:
                validate_phone_number(phone)
            except ValidationError:
                raise

            phone_exists = self.uow.vip_clients.find_by_phone(phone)
            if phone_exists:
                raise PhoneAlreadyTakenError()

            client_code_exists = self.uow.vip_clients.find_by_client_code(
                data.client_code
            )
            if client_code_exists:
                raise ClientCodeAlreadyTakenError()

            vip_client = VipClient.create(
                first_name=data.first_name,
                last_name=data.last_name,
                email=email,
                phone=phone,
                client_code=ClientCode(data.client_code),
            )
            self.uow.vip_clients.create(vip_client)

            event = vip_client.create_vip_client_email_request()

            return event
