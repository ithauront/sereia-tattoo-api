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


def test_send_forgot_password_email_success(write_uow, make_user):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

    use_case = PrepareSendForgotPasswordEmailUseCase(write_uow)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    assert user.password_token_version == 0

    result = use_case.execute(input_data)

    assert result is not None
    assert isinstance(result, PasswordResetEmailRequested)
    assert result.email == "jhon@doe.com"
    assert type(result.user_id) is UUID
    assert type(result.password_token_version) is int
    assert result.password_token_version == 1
    assert user.password_token_version == 1
    assert user.activation_token_version == 0
    assert user.id == result.user_id


def test_send_forgot_password_email_user_not_found(write_uow):
    use_case = PrepareSendForgotPasswordEmailUseCase(write_uow)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)


def test_send_forgot_password_email_user_inactive(write_uow, read_uow, make_user):
    user = make_user(email="jhon@doe.com", is_active=False)
    write_uow.users.create(user)

    use_case = PrepareSendForgotPasswordEmailUseCase(read_uow)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserInactiveError):
        use_case.execute(input_data)
