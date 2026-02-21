import pytest
from app.application.studio.use_cases.DTO.first_activation_user_dto import (
    FirstActivationInput,
)
from app.application.studio.use_cases.users_use_cases.first_activation_user import (
    FirstActivationUserUseCase,
)
from app.core.exceptions.users import (
    InvalidActivationTokenError,
    UserActivatedBeforeError,
    UserNotFoundError,
    UsernameAlreadyTakenError,
)
from app.core.exceptions.validation import ValidationError
from app.core.security.passwords import verify_password


def test_first_activation_of_user_success(users_repo, make_user):
    user = make_user(
        has_activated_once=False,
        is_active=False,
        activation_token_version=0,
        username="",
    )
    users_repo.create(user)
    use_case = FirstActivationUserUseCase(users_repo)
    dto = FirstActivationInput(
        user_id=user.id, token_version=0, username="JhonDoe", password="JhonDoe1"
    )

    use_case.execute(dto)

    assert user.username == "JhonDoe"
    assert verify_password("JhonDoe1", user.hashed_password) is True
    assert user.has_activated_once is True
    assert user.is_active is True
    assert user.activation_token_version == 1


def test_not_user_cannot_be_activated(users_repo, make_user):
    user = make_user(
        has_activated_once=False,
        is_active=False,
        activation_token_version=0,
        username="",
    )
    use_case = FirstActivationUserUseCase(users_repo)
    dto = FirstActivationInput(
        user_id=user.id, token_version=0, username="JhonDoe", password="JhonDoe1"
    )
    with pytest.raises(UserNotFoundError):
        use_case.execute(dto)

    assert user.username == ""
    assert user.has_activated_once is False
    assert user.is_active is False
    assert user.activation_token_version == 0


def test_user_activated_before_cannot_be_first_activated(users_repo, make_user):
    user = make_user(
        has_activated_once=True,
        is_active=False,
        activation_token_version=1,
        username="",
    )
    users_repo.create(user)
    use_case = FirstActivationUserUseCase(users_repo)
    dto = FirstActivationInput(
        user_id=user.id, token_version=1, username="JhonDoe", password="JhonDoe1"
    )
    with pytest.raises(UserActivatedBeforeError):
        use_case.execute(dto)

    assert user.username == ""
    assert user.has_activated_once is True
    assert user.is_active is False
    assert user.activation_token_version == 1


def test_invalid_token_version(users_repo, make_user):
    user = make_user(
        has_activated_once=False,
        is_active=False,
        activation_token_version=0,
        username="",
    )
    users_repo.create(user)
    use_case = FirstActivationUserUseCase(users_repo)
    dto = FirstActivationInput(
        user_id=user.id, token_version=1, username="JhonDoe", password="JhonDoe1"
    )
    with pytest.raises(InvalidActivationTokenError):
        use_case.execute(dto)

    assert user.username == ""
    assert user.has_activated_once is False
    assert user.is_active is False
    assert user.activation_token_version == 0


def test_invalid_username(users_repo, make_user):
    user = make_user(
        has_activated_once=False,
        is_active=False,
        activation_token_version=0,
        username="",
    )
    users_repo.create(user)
    use_case = FirstActivationUserUseCase(users_repo)
    dto = FirstActivationInput(
        user_id=user.id, token_version=0, username="jh", password="JhonDoe1"
    )
    with pytest.raises(ValidationError) as exception:
        use_case.execute(dto)

    assert str(exception.value) == "username_must_have_between_3_and_30_characters"
    assert user.username == ""
    assert user.has_activated_once is False
    assert user.is_active is False
    assert user.activation_token_version == 0


def test_username_already_taken(users_repo, make_user):
    first_user = make_user(username="JhonDoe")
    users_repo.create(first_user)
    user = make_user(
        has_activated_once=False,
        is_active=False,
        activation_token_version=0,
        username="",
    )
    users_repo.create(user)

    use_case = FirstActivationUserUseCase(users_repo)
    dto = FirstActivationInput(
        user_id=user.id, token_version=0, username="JhonDoe", password="JhonDoe1"
    )
    with pytest.raises(UsernameAlreadyTakenError):
        use_case.execute(dto)

    assert user.username == ""
    assert user.has_activated_once is False
    assert user.is_active is False
    assert user.activation_token_version == 0


def test_invalid_password(users_repo, make_user):

    user = make_user(
        has_activated_once=False,
        is_active=False,
        activation_token_version=0,
        username="",
    )
    users_repo.create(user)

    use_case = FirstActivationUserUseCase(users_repo)
    dto = FirstActivationInput(
        user_id=user.id, token_version=0, username="JhonDoe", password="Jhon Doe 1"
    )
    with pytest.raises(ValidationError) as exception:
        use_case.execute(dto)

    assert str(exception.value) == "password_cannot_contain_spaces"
    assert user.username == ""
    assert user.has_activated_once is False
    assert user.is_active is False
    assert user.activation_token_version == 0
