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


def test_resend_activation_email_success(write_uow, make_user):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

    use_case = PrepareResendActivationEmailUseCase(write_uow)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    assert user.activation_token_version == 0

    result = use_case.execute(input_data)

    assert result is not None
    assert isinstance(result, ActivationEmailRequested)
    assert result.email == "jhon@doe.com"
    assert type(result.user_id) is UUID
    assert type(result.activation_token_version) is int
    assert result.activation_token_version == 1
    assert user.activation_token_version == 1
    assert user.id == result.user_id


def test_resend_activation_email_user_not_found(write_uow):
    use_case = PrepareResendActivationEmailUseCase(write_uow)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)


def test_user_already_activated_once(write_uow, make_user):
    user = make_user(email="jhon@doe.com", has_activated_once=True)
    write_uow.users.create(user)

    use_case = PrepareResendActivationEmailUseCase(write_uow)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")

    with pytest.raises(UserActivatedBeforeError):
        use_case.execute(input_data)


def test_find_by_email_called_before_resend(mocker, make_user, write_uow):
    user = make_user(email="jhon@doe.com", has_activated_once=False)
    write_uow.users.create(user)
    spy = mocker.spy(write_uow.users, "find_by_email")

    use_case = PrepareResendActivationEmailUseCase(write_uow)
    input_data = PrepareResendActivationEmailInput(user_email="jhon@doe.com")
    use_case.execute(input_data)

    spy.assert_called_once_with("jhon@doe.com")
