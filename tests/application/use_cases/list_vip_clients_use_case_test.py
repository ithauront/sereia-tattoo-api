from pydantic import ValidationError
import pytest
from freezegun import freeze_time

from app.application.studio.use_cases.DTO.get_users_dto import (
    ListVipClientsInput,
)
from app.application.studio.use_cases.users_use_cases.list_vip_clients import (
    ListVipClientsUseCase,
)


def test_list_vip_clients_default_success(read_uow, write_uow, make_vip_client):
    vip_client1 = make_vip_client(first_name="Daniela")
    vip_client2 = make_vip_client(first_name="Carla")
    vip_client3 = make_vip_client(first_name="Bernard")
    vip_client4 = make_vip_client(first_name="Adonis")

    write_uow.vip_clients.create(vip_client1)
    write_uow.vip_clients.create(vip_client2)
    write_uow.vip_clients.create(vip_client3)
    write_uow.vip_clients.create(vip_client4)
    use_case = ListVipClientsUseCase(read_uow)
    input_data = ListVipClientsInput()

    result = use_case.execute(input_data)

    assert result.vip_clients is not None
    assert result.vip_clients[0].first_name == "Adonis"
    assert result.vip_clients[1].first_name == "Bernard"
    assert result.vip_clients[2].first_name == "Carla"
    assert result.vip_clients[3].first_name == "Daniela"


def test_list_vip_clients_descendent_success(read_uow, write_uow, make_vip_client):
    vip_client1 = make_vip_client(first_name="Daniela")
    vip_client2 = make_vip_client(first_name="Carla")
    vip_client3 = make_vip_client(first_name="Bernard")
    vip_client4 = make_vip_client(first_name="Adonis")

    write_uow.vip_clients.create(vip_client1)
    write_uow.vip_clients.create(vip_client2)
    write_uow.vip_clients.create(vip_client3)
    write_uow.vip_clients.create(vip_client4)
    use_case = ListVipClientsUseCase(read_uow)
    input_data = ListVipClientsInput(direction="desc")

    result = use_case.execute(input_data)

    assert result.vip_clients is not None
    assert result.vip_clients[0].first_name == "Daniela"
    assert result.vip_clients[1].first_name == "Carla"
    assert result.vip_clients[2].first_name == "Bernard"
    assert result.vip_clients[3].first_name == "Adonis"


def test_list_vip_clients_last_name_success(read_uow, write_uow, make_vip_client):
    vip_client1 = make_vip_client(last_name="Dumas")
    vip_client2 = make_vip_client(last_name="Correia")
    vip_client3 = make_vip_client(last_name="Bispo")
    vip_client4 = make_vip_client(last_name="Americo")

    write_uow.vip_clients.create(vip_client1)
    write_uow.vip_clients.create(vip_client2)
    write_uow.vip_clients.create(vip_client3)
    write_uow.vip_clients.create(vip_client4)
    use_case = ListVipClientsUseCase(read_uow)
    input_data = ListVipClientsInput(order_by="last_name")

    result = use_case.execute(input_data)

    assert result.vip_clients is not None
    assert result.vip_clients[0].last_name == "Americo"
    assert result.vip_clients[1].last_name == "Bispo"
    assert result.vip_clients[2].last_name == "Correia"
    assert result.vip_clients[3].last_name == "Dumas"


@freeze_time("2025-01-01")
def test_list_by_created_at_success(read_uow, write_uow, make_vip_client):
    vip_client1 = make_vip_client(first_name="Daniela")
    write_uow.vip_clients.create(vip_client1)

    with freeze_time("2025-01-02"):
        vip_client2 = make_vip_client(first_name="Carla")
        write_uow.vip_clients.create(vip_client2)

    with freeze_time("2025-01-03"):
        vip_client3 = make_vip_client(first_name="Bernard")
        write_uow.vip_clients.create(vip_client3)

    with freeze_time("2025-01-04"):
        vip_client4 = make_vip_client(first_name="Adonis")
        write_uow.vip_clients.create(vip_client4)

    use_case = ListVipClientsUseCase(read_uow)
    input_data = ListVipClientsInput(order_by="created_at")

    result = use_case.execute(input_data)

    assert result.vip_clients is not None
    assert result.vip_clients[0].first_name == "Daniela"
    assert result.vip_clients[1].first_name == "Carla"
    assert result.vip_clients[2].first_name == "Bernard"
    assert result.vip_clients[3].first_name == "Adonis"


def test_pagination_and_limit_success(read_uow, write_uow, make_vip_client):
    for i in range(16):
        letter = chr(ord("a") + i)
        vip_client = make_vip_client(first_name=f"vip_client{letter}")
        write_uow.vip_clients.create(vip_client)

    use_case = ListVipClientsUseCase(read_uow)
    input_data = ListVipClientsInput(page=2, limit=10)

    result = use_case.execute(input_data)

    assert result.vip_clients is not None
    assert len(result.vip_clients) == 6
    assert result.vip_clients[0].first_name == "vip_clientk"  # 11th letter
    assert result.vip_clients[-1].first_name == "vip_clientp"  # 16th letter


def test_empty_db(read_uow):

    use_case = ListVipClientsUseCase(read_uow)
    input_data = ListVipClientsInput()

    result = use_case.execute(input_data)

    assert result.vip_clients == []
    assert len(result.vip_clients) == 0


# DTO for listVipClientsUseCase tests
def test_page_cannot_be_less_than_one():
    with pytest.raises(ValidationError):
        ListVipClientsInput(page=0)


def test_limit_cannot_be_less_than_one():
    with pytest.raises(ValidationError):
        ListVipClientsInput(limit=0)
