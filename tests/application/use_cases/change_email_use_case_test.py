from pydantic import ValidationError
import pytest
from app.application.studio.use_cases.DTO.change_email_dto import ChangeEmailInput
from app.application.studio.use_cases.users_use_cases.change_email import (
    ChangeEmailUseCase,
)
from app.core.exceptions.users import AuthenticationFailedError, EmailAlreadyTakenError


def test_change_email(users_repo, make_user):
    user = make_user(access_token_version=0, refresh_token_version=0)
    users_repo.create(user)

    use_case = ChangeEmailUseCase(users_repo)
    input_data = ChangeEmailInput(password="123456", new_email="new@email.com")

    use_case.execute(input_data, user)

    saved = users_repo.find_by_id(user.id)
    assert saved.email == "new@email.com"
    assert saved.access_token_version == 1
    assert saved.refresh_token_version == 1


def test_change_to_same_email_should_pass(users_repo, make_user):
    user = make_user(email="jhon@doe.com")
    users_repo.create(user)

    use_case = ChangeEmailUseCase(users_repo)
    input_data = ChangeEmailInput(password="123456", new_email="jhon@doe.com")

    use_case.execute(input_data, user)

    saved = users_repo.find_by_id(user.id)
    assert saved.email == "jhon@doe.com"


def test_change_email_wrond_password(users_repo, make_user):
    user = make_user(access_token_version=0, refresh_token_version=0)
    users_repo.create(user)

    use_case = ChangeEmailUseCase(users_repo)
    input_data = ChangeEmailInput(password="wrong_password", new_email="new@email.com")

    with pytest.raises(AuthenticationFailedError):
        use_case.execute(input_data, user)

    assert user.access_token_version == 0
    assert user.refresh_token_version == 0


def test_change_email_already_in_use(users_repo, make_user):
    user1 = make_user(email="taken@email.com")
    user2 = make_user(email="new_user@email.com")
    users_repo.create(user1)
    users_repo.create(user2)

    use_case = ChangeEmailUseCase(users_repo)
    input_data = ChangeEmailInput(password="123456", new_email="taken@email.com")

    with pytest.raises(EmailAlreadyTakenError):
        use_case.execute(input_data, user2)


def test_change_email_email_not_valid():
    # dto test
    with pytest.raises(ValidationError):
        ChangeEmailInput(password="wrong_password", new_email="wrong_email_format")
