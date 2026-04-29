import pytest

from app.application.studio.use_cases.DTO.get_users_dto import GetVipClientInput
from app.application.studio.use_cases.DTO.vip_client_output import (
    VipClientOutput,
    VipClientOutputWithDetails,
)

from app.application.studio.use_cases.users_use_cases.get_vip_client import (
    GetVipClientUseCase,
)
from app.core.exceptions.users import VipClientNotFoundError
from app.core.types.client_credit_source_type import ClientCreditSourceType


def test_get_vip_client_success(
    read_uow, write_uow, make_vip_client, make_client_credit_entry
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )
    write_uow.client_credit_entries.create(entry)

    use_case = GetVipClientUseCase(read_uow)
    dto = GetVipClientInput(vip_client_id=vip_client.id)

    result = use_case.execute(dto)

    assert result is not None
    assert result.vip_client.first_name == "Jhon"
    assert result.vip_client.client_code == "JHON-BLUE"
    assert result.balance == 10
    assert isinstance(result, VipClientOutputWithDetails)
    assert isinstance(result.vip_client, VipClientOutput)
    assert isinstance(result.balance, int)


def test_get_vip_client_with_no_credits_success(read_uow, write_uow, make_vip_client):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    use_case = GetVipClientUseCase(read_uow)
    dto = GetVipClientInput(vip_client_id=vip_client.id)

    result = use_case.execute(dto)

    assert result.balance == 0


def test_get_vip_client_with_negative_credits_success(
    read_uow, write_uow, make_vip_client, make_client_credit_entry
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
    )
    write_uow.client_credit_entries.create(entry)

    use_case = GetVipClientUseCase(read_uow)
    dto = GetVipClientInput(vip_client_id=vip_client.id)

    result = use_case.execute(dto)

    assert result.balance == -10


def test_get_vip_client_with_multiple_credits_success(
    read_uow, write_uow, make_vip_client, make_client_credit_entry
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
    )
    write_uow.client_credit_entries.create(entry)
    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )
    write_uow.client_credit_entries.create(entry)
    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )
    write_uow.client_credit_entries.create(entry)

    use_case = GetVipClientUseCase(read_uow)
    dto = GetVipClientInput(vip_client_id=vip_client.id)

    result = use_case.execute(dto)

    assert result.balance == 10


def test_get_right_vip_client_credits_success(
    read_uow, write_uow, make_vip_client, make_client_credit_entry
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    wrong_vip_client = make_vip_client(
        first_name="Jane",
        last_name="Doe",
        email="jane@doe.com",
        phone="71988888888",
        client_code="JANE-RED",
    )
    write_uow.vip_clients.create(wrong_vip_client)
    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
    )
    write_uow.client_credit_entries.create(entry)
    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )
    write_uow.client_credit_entries.create(entry)
    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=wrong_vip_client.id,
    )
    write_uow.client_credit_entries.create(entry)

    use_case = GetVipClientUseCase(read_uow)
    dto = GetVipClientInput(vip_client_id=vip_client.id)

    result = use_case.execute(dto)

    assert result.balance == 0


def test_vip_client_not_found(read_uow, make_vip_client):
    vip_client = make_vip_client()
    # do not persist vip_client

    use_case = GetVipClientUseCase(read_uow)
    dto = GetVipClientInput(vip_client_id=vip_client.id)

    with pytest.raises(VipClientNotFoundError):
        use_case.execute(dto)
