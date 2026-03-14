from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork
from app.application.studio.use_cases.DTO.change_phone_dto import (
    ChangeVipClientPhoneInput,
)
from app.core.exceptions.users import PhoneAlreadyTakenError, VipClientNotFoundError
from app.core.normalize.normalize_phone import normalize_phone
from app.core.validations.phone_number import validate_phone_number


class ChangeVipClientPhoneUseCase:
    def __init__(self, uow: WriteUnitOfWork):
        self.uow = uow

    def execute(self, data: ChangeVipClientPhoneInput):
        with self.uow:
            vip_client = self.uow.vip_clients.find_by_id(data.vip_client_id)

            if not vip_client:
                raise VipClientNotFoundError()

            new_phone = normalize_phone(data.new_phone)
            validate_phone_number(new_phone)

            if vip_client.phone == new_phone:
                return

            if self.uow.vip_clients.find_by_phone(new_phone):
                raise PhoneAlreadyTakenError()

            vip_client.change_phone(new_phone)

            self.uow.vip_clients.update(vip_client)
