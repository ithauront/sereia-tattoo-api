from uuid import UUID

import pytest
from app.core.exceptions.users import (
    UserInactiveError,
    UserNotFoundError,
)
from app.domain.users.entities.user import User
from app.domain.users.use_cases.DTO.prepare_send_forgot_password_email_dto import (
    PrepareSendForgotPasswordEmailInput,
)
from app.domain.users.use_cases.prepare_send_forgot_password_email import (
    PrepareSendForgotPasswordEmailUseCase,
)


def test_send_forgot_password_email_success(repo, make_user):
    user = make_user(email="jhon@doe.com")
    repo.create(user)

    use_case = PrepareSendForgotPasswordEmailUseCase(repo)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    assert user.password_token_version == 0

    result = use_case.execute(input_data)

    assert result is not None
    assert isinstance(result, User)
    assert result.email == "jhon@doe.com"
    assert type(result.id) is UUID
    assert type(result.activation_token_version) is int
    assert result.activation_token_version == 0
    assert user.activation_token_version == 0
    assert user.id == result.id


def test_send_forgot_password_email_user_not_found(repo, mocker):
    use_case = PrepareSendForgotPasswordEmailUseCase(repo)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)


def test_send_forgot_password_email_user_inactive(repo, make_user, mocker):
    user = make_user(email="jhon@doe.com", is_active=False)
    repo.create(user)

    use_case = PrepareSendForgotPasswordEmailUseCase(repo)
    input_data = PrepareSendForgotPasswordEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserInactiveError):
        use_case.execute(input_data)
