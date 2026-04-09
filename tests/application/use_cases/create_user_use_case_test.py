from uuid import UUID
from pydantic import ValidationError
import pytest
from app.application.studio.use_cases.DTO.create_user_dto import CreateUserInput
from app.application.studio.use_cases.users_use_cases.create_user import (
    CreateUserUseCase,
)
from app.core.exceptions.users import UserAlreadyExistsError
from app.domain.studio.users.events.activation_email_requested import (
    ActivationEmailRequested,
)
from tests.fakes.fake_event_bus import FakeEventBus


@pytest.mark.asyncio
async def test_create_user_success(write_uow, read_uow):

    event_bus = FakeEventBus()

    use_case = CreateUserUseCase(write_uow, event_bus)
    input_data = CreateUserInput(user_email="jhon@doe.com")

    await use_case.execute(input_data)

    saved_user = read_uow.users.find_by_email("jhon@doe.com")
    assert saved_user is not None
    assert saved_user.email == "jhon@doe.com"
    assert saved_user.has_activated_once is False

    assert len(event_bus.events) == 1
    event = event_bus.events[0]

    assert isinstance(event, ActivationEmailRequested)
    assert event.email == "jhon@doe.com"
    assert type(event.user_id) is UUID
    assert type(event.activation_token_version) is int
    assert event.activation_token_version == 1

    assert saved_user.id == event.user_id


@pytest.mark.asyncio
async def test_user_already_exists(write_uow, make_user, mocker):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

    event_bus = FakeEventBus()

    spy = mocker.spy(write_uow.users, "create")

    use_case = CreateUserUseCase(write_uow, event_bus)
    input_data = CreateUserInput(user_email="jhon@doe.com")

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(input_data)

    spy.assert_not_called()
    assert len(event_bus.events) == 0


def test_user_email_not_valid(write_uow, read_uow, mocker):
    spy = mocker.spy(write_uow.users, "create")

    with pytest.raises(ValidationError):
        CreateUserInput(user_email="not_an_email")

    saved_user = read_uow.users.find_by_email("not_an_email")
    assert saved_user is None
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_find_by_email_called_before_create(mocker, write_uow):
    spy = mocker.spy(write_uow.users, "find_by_email")

    event_bus = FakeEventBus()

    use_case = CreateUserUseCase(write_uow, event_bus)
    await use_case.execute(CreateUserInput(user_email="jhon@doe.com"))

    spy.assert_called_once_with("jhon@doe.com")

    assert len(event_bus.events) == 1
