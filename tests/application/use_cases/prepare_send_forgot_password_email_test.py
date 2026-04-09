from uuid import UUID
import pytest
from app.application.studio.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)
from app.application.studio.use_cases.users_use_cases.prepare_send_forgot_password_email import (
    PrepareSendForgotPasswordEmailUseCase,
)
from app.core.exceptions.users import (
    UserInactiveError,
    UserNotFoundError,
)
from app.domain.studio.users.events.password_reset_email_requested import (
    PasswordResetEmailRequested,
)
from tests.fakes.fake_event_bus import FakeEventBus


@pytest.mark.asyncio
async def test_send_forgot_password_email_success(write_uow, make_user):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

    event_bus = FakeEventBus()

    use_case = PrepareSendForgotPasswordEmailUseCase(write_uow, event_bus)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    assert user.password_token_version == 0

    await use_case.execute(input_data)

    assert len(event_bus.events) == 1
    event = event_bus.events[0]

    assert event is not None
    assert isinstance(event, PasswordResetEmailRequested)
    assert event.email == "jhon@doe.com"
    assert type(event.user_id) is UUID
    assert type(event.password_token_version) is int
    assert event.password_token_version == 1
    assert user.password_token_version == 1
    assert user.activation_token_version == 0
    assert user.id == event.user_id


@pytest.mark.asyncio
async def test_send_forgot_password_email_user_not_found(write_uow):
    event_bus = FakeEventBus()

    use_case = PrepareSendForgotPasswordEmailUseCase(write_uow, event_bus)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserNotFoundError):
        await use_case.execute(input_data)


@pytest.mark.asyncio
async def test_send_forgot_password_email_user_inactive(write_uow, read_uow, make_user):
    user = make_user(email="jhon@doe.com", is_active=False)
    write_uow.users.create(user)

    event_bus = FakeEventBus()

    use_case = PrepareSendForgotPasswordEmailUseCase(read_uow, event_bus)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserInactiveError):
        await use_case.execute(input_data)
