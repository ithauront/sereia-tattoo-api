from uuid import UUID
import pytest
from app.application.studio.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.application.studio.use_cases.users_use_cases.prepare_resend_activation_email import (
    PrepareResendActivationEmailUseCase,
)
from app.core.exceptions.users import UserActivatedBeforeError, UserNotFoundError
from app.domain.studio.users.events.activation_email_requested import (
    ActivationEmailRequested,
)
from tests.fakes.fake_event_bus import FakeEventBus


@pytest.mark.asyncio
async def test_resend_activation_email_success(
    write_uow,
    make_user,
):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

    event_bus = FakeEventBus()

    use_case = PrepareResendActivationEmailUseCase(write_uow, event_bus)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    assert user.activation_token_version == 0

    await use_case.execute(input_data)

    assert len(event_bus.events) == 1
    event = event_bus.events[0]

    assert isinstance(event, ActivationEmailRequested)
    assert event.email == "jhon@doe.com"
    assert type(event.user_id) is UUID
    assert type(event.activation_token_version) is int
    assert event.activation_token_version == 1
    assert user.activation_token_version == 1
    assert user.id == event.user_id


@pytest.mark.asyncio
async def test_resend_activation_email_user_not_found(write_uow):

    event_bus = FakeEventBus()

    use_case = PrepareResendActivationEmailUseCase(write_uow, event_bus)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserNotFoundError):
        await use_case.execute(input_data)


@pytest.mark.asyncio
async def test_user_already_activated_once(write_uow, make_user):
    user = make_user(email="jhon@doe.com", has_activated_once=True)
    write_uow.users.create(user)
    event_bus = FakeEventBus()

    use_case = PrepareResendActivationEmailUseCase(write_uow, event_bus)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserActivatedBeforeError):
        await use_case.execute(input_data)


@pytest.mark.asyncio
async def test_find_by_email_called_before_resend(mocker, make_user, write_uow):
    user = make_user(email="jhon@doe.com", has_activated_once=False)
    write_uow.users.create(user)
    event_bus = FakeEventBus()
    spy = mocker.spy(write_uow.users, "find_by_email")

    use_case = PrepareResendActivationEmailUseCase(write_uow, event_bus)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")
    await use_case.execute(input_data)

    spy.assert_called_once_with("jhon@doe.com")
