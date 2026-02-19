from uuid import UUID

import pytest
from app.core.exceptions.users import UserActivatedBeforeError, UserNotFoundError
from app.domain.users.entities.user import User
from app.domain.users.use_cases.DTO.prepare_resend_activation_email_dto import (
    PrepareResendActivationEmailInput,
)
from app.domain.users.use_cases.prepare_resend_activation_email import (
    PrepareResendActivationEmailUseCase,
)


def test_resend_activation_email_success(users_repo, make_user):
    user = make_user(email="jhon@doe.com")
    users_repo.create(user)

    use_case = PrepareResendActivationEmailUseCase(users_repo)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    assert user.activation_token_version == 0

    result = use_case.execute(input_data)

    assert result is not None
    assert isinstance(result, User)
    assert result.email == "jhon@doe.com"
    assert type(result.id) is UUID
    assert type(result.activation_token_version) is int
    assert result.activation_token_version == 0
    assert user.activation_token_version == 0
    assert user.id == result.id


def test_resend_activation_email_user_not_found(users_repo, mocker):
    use_case = PrepareResendActivationEmailUseCase(users_repo)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)


def test_user_already_activated_once(users_repo, make_user, mocker):
    user = make_user(email="jhon@doe.com", has_activated_once=True)
    users_repo.create(user)

    use_case = PrepareResendActivationEmailUseCase(users_repo)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserActivatedBeforeError):
        use_case.execute(input_data)


def test_find_by_email_called_before_resend(mocker, make_user, users_repo):
    user = make_user(email="jhon@doe.com", has_activated_once=False)
    users_repo.create(user)
    spy = mocker.spy(users_repo, "find_by_email")

    use_case = PrepareResendActivationEmailUseCase(users_repo)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")
    use_case.execute(input_data)

    spy.assert_called_once_with("jhon@doe.com")
