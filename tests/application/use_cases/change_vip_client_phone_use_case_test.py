import pytest

from app.application.studio.use_cases.DTO.change_phone_dto import (
    ChangeVipClientPhoneInput,
)
from app.application.studio.use_cases.users_use_cases.change_vip_client_phone import (
    ChangeVipClientPhoneUseCase,
)
from app.core.exceptions.users import PhoneAlreadyTakenError, VipClientNotFoundError
from app.core.exceptions.validation import ValidationError


def test_change_vip_client_phone_success(write_uow, read_uow, make_vip_client):
    vip_client = make_vip_client(phone="71999999999")
    write_uow.vip_clients.create(vip_client)

    use_case = ChangeVipClientPhoneUseCase(write_uow)
    input_data = ChangeVipClientPhoneInput(
        new_phone="71-9888 88888", vip_client_id=vip_client.id
    )

    use_case.execute(input_data)

    saved = read_uow.vip_clients.find_by_id(vip_client.id)
    assert saved.phone == "71988888888"  # phone normalized
    assert read_uow.vip_clients.find_by_phone("71999999999") is None


def test_change_vip_client_phone_to_same_phone_success(
    write_uow, read_uow, make_vip_client
):
    vip_client = make_vip_client(phone="71999999999")
    write_uow.vip_clients.create(vip_client)

    use_case = ChangeVipClientPhoneUseCase(write_uow)
    input_data = ChangeVipClientPhoneInput(
        new_phone="71999999999", vip_client_id=vip_client.id
    )

    use_case.execute(input_data)

    saved = read_uow.vip_clients.find_by_id(vip_client.id)
    assert saved.phone == "71999999999"


def test_change_vip_client_phone_client_not_found(write_uow, make_vip_client):
    vip_client = make_vip_client(phone="71999999999")

    use_case = ChangeVipClientPhoneUseCase(write_uow)
    input_data = ChangeVipClientPhoneInput(
        new_phone="71988888888", vip_client_id=vip_client.id
    )

    with pytest.raises(VipClientNotFoundError):
        use_case.execute(input_data)


def test_change_vip_client_phone_validation_error(write_uow, read_uow, make_vip_client):
    vip_client = make_vip_client(phone="71999999999")
    write_uow.vip_clients.create(vip_client)

    use_case = ChangeVipClientPhoneUseCase(write_uow)
    input_data = ChangeVipClientPhoneInput(
        new_phone="71988", vip_client_id=vip_client.id
    )  # Phone to small

    with pytest.raises(ValidationError):
        use_case.execute(input_data)

    saved = read_uow.vip_clients.find_by_id(vip_client.id)
    assert saved.phone == "71999999999"


def test_change_vip_client_phone_already_taken(write_uow, read_uow, make_vip_client):
    vip_client1 = make_vip_client(phone="71999999999")
    write_uow.vip_clients.create(vip_client1)
    vip_client2 = make_vip_client(phone="71888888888")
    write_uow.vip_clients.create(vip_client2)

    use_case = ChangeVipClientPhoneUseCase(write_uow)
    input_data = ChangeVipClientPhoneInput(
        new_phone="71999999999", vip_client_id=vip_client2.id
    )  # Same phone of vip_client1

    with pytest.raises(PhoneAlreadyTakenError):
        use_case.execute(input_data)

    saved_vip_client1 = read_uow.vip_clients.find_by_id(vip_client1.id)
    assert saved_vip_client1.phone == "71999999999"
    saved_vip_client2 = read_uow.vip_clients.find_by_id(vip_client2.id)
    assert saved_vip_client2.phone == "71888888888"
