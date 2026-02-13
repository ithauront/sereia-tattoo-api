from uuid import UUID
from pydantic import ValidationError
import pytest
from app.core.exceptions.users import UserAlreadyExistsError
from app.domain.users.events.activation_email_requested import ActivationEmailRequested
from app.domain.users.use_cases.DTO.create_user_dto import CreateUserInput
from app.domain.users.use_cases.create_user import CreateUserUseCase


def test_create_user_success(repo):
    use_case = CreateUserUseCase(repo)
    input_data = CreateUserInput(user_email="jhon@doe.com")

    result = use_case.execute(input_data)

    saved_user = repo.find_by_email("jhon@doe.com")
    assert saved_user is not None
    assert saved_user.email == "jhon@doe.com"
    assert saved_user.has_activated_once is False

    assert result is not None
    assert isinstance(result, ActivationEmailRequested)
    assert result.email == "jhon@doe.com"
    assert type(result.user_id) is UUID
    assert type(result.activation_token_version) is int
    assert result.activation_token_version == 0
    assert saved_user.id == result.user_id


def test_user_already_exists(repo, make_user, mocker):
    user = make_user(email="jhon@doe.com")
    repo.create(user)

    spy = mocker.spy(repo, "create")
    use_case = CreateUserUseCase(repo)
    input_data = CreateUserInput(user_email="jhon@doe.com")

    with pytest.raises(UserAlreadyExistsError):
        use_case.execute(input_data)

    spy.assert_not_called()


def test_user_email_not_valid(repo, mocker):
    spy = mocker.spy(repo, "create")

    with pytest.raises(ValidationError):
        CreateUserInput(user_email="not_an_email")

    saved_user = repo.find_by_email("not_an_email")
    assert saved_user is None
    spy.assert_not_called()


def test_find_by_email_called_before_create(mocker, repo):
    spy = mocker.spy(repo, "find_by_email")

    use_case = CreateUserUseCase(repo)
    use_case.execute(CreateUserInput(user_email="jhon@doe.com"))

    spy.assert_called_once_with("jhon@doe.com")
