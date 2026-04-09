import pytest

from app.application.studio.use_cases.DTO.create_vip_client_dto import (
    CreateVipClientInput,
)
from app.application.studio.use_cases.users_use_cases.create_vip_client import (
    CreateVipClientUseCase,
)
from app.core.exceptions.users import (
    ClientCodeAlreadyTakenError,
    EmailAlreadyTakenError,
    PhoneAlreadyTakenError,
)
from app.core.exceptions.validation import ValidationError
from app.domain.studio.users.events.create_vip_client_email_requested import (
    CreateVipClientEmailRequested,
)
from tests.fakes.fake_event_bus import FakeEventBus


@pytest.mark.asyncio
async def test_create_vip_client_success(write_uow, read_uow):

    event_bus = FakeEventBus()

    use_case = CreateVipClientUseCase(write_uow, event_bus)
    input_data = CreateVipClientInput(
        first_name="Jhon",
        last_name="Doe",
        phone="11-92345-6789",  # we test normalization of phone
        email="JHON@DOE.com",  # we test normalization of email string
        client_code="JHON-AZUL",
    )

    await use_case.execute(input_data)

    saved_vip_client = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert saved_vip_client is not None
    assert saved_vip_client.phone == "11923456789"  # normalized
    assert saved_vip_client.email == "jhon@doe.com"  # normalized
    assert saved_vip_client.client_code.value == "JHON-AZUL"

    assert len(event_bus.events) == 1
    event = event_bus.events[0]

    assert event is not None
    assert isinstance(event, CreateVipClientEmailRequested)
    assert event.email == "jhon@doe.com"
    assert event.client_code == "JHON-AZUL"


@pytest.mark.asyncio
async def test_vip_client_invalid_phone(write_uow, mocker):
    event_bus = FakeEventBus()

    spy = mocker.spy(write_uow.vip_clients, "create")

    use_case = CreateVipClientUseCase(write_uow, event_bus)

    input_data = CreateVipClientInput(
        first_name="Jhon",
        last_name="Doe",
        phone="invalid-phone",
        email="jhon@doe.com",
        client_code="JHON-AZUL",
    )

    with pytest.raises(ValidationError):
        await use_case.execute(input_data)

    spy.assert_not_called()


@pytest.mark.asyncio
async def test_vip_client_email_taken(write_uow, make_vip_client, mocker):
    event_bus = FakeEventBus()
    vip_client = make_vip_client(
        email="jhon@doe.com", phone="11888888888", client_code="OTHER-CODE"
    )
    write_uow.vip_clients.create(vip_client)

    spy = mocker.spy(write_uow.vip_clients, "create")

    use_case = CreateVipClientUseCase(write_uow, event_bus)
    input_data = CreateVipClientInput(
        first_name="Jhon",
        last_name="Doe",
        phone="11923456789",
        email="jhon@doe.com",
        client_code="JHON-AZUL",
    )

    with pytest.raises(EmailAlreadyTakenError):
        await use_case.execute(input_data)

    spy.assert_not_called()


@pytest.mark.asyncio
async def test_vip_client_phone_taken(write_uow, make_vip_client, mocker):
    event_bus = FakeEventBus()
    vip_client = make_vip_client(
        email="other@doe.com", phone="11923456789", client_code="OTHER-CODE"
    )
    write_uow.vip_clients.create(vip_client)

    spy = mocker.spy(write_uow.vip_clients, "create")

    use_case = CreateVipClientUseCase(write_uow, event_bus)
    input_data = CreateVipClientInput(
        first_name="Jhon",
        last_name="Doe",
        phone="11923456789",
        email="jhon@doe.com",
        client_code="JHON-AZUL",
    )

    with pytest.raises(PhoneAlreadyTakenError):
        await use_case.execute(input_data)

    spy.assert_not_called()


@pytest.mark.asyncio
async def test_vip_client_client_code_taken(write_uow, make_vip_client, mocker):
    event_bus = FakeEventBus()
    vip_client = make_vip_client(
        email="other@doe.com", phone="11888888888", client_code="JHON-AZUL"
    )
    write_uow.vip_clients.create(vip_client)

    spy = mocker.spy(write_uow.vip_clients, "create")

    use_case = CreateVipClientUseCase(write_uow, event_bus)
    input_data = CreateVipClientInput(
        first_name="Jhon",
        last_name="Doe",
        phone="11923456789",
        email="jhon@doe.com",
        client_code="JHON-AZUL",
    )

    with pytest.raises(ClientCodeAlreadyTakenError):
        await use_case.execute(input_data)

    spy.assert_not_called()
