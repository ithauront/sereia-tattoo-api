import pytest
from app.domain.users.use_cases.DTO.login_dto import LoginInput
from app.domain.users.use_cases.login_user import LoginUserUseCase


def test_login_sucess(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = LoginUserUseCase(repo)
    input_data = LoginInput(identifier="JhonDoe", password="123456")

    result = use_case.execute(input_data)

    assert result.access_token is not None
    assert result.refresh_token is not None
    assert len(result.access_token) > 10
    assert len(result.refresh_token) > 10


def test_user_not_found(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = LoginUserUseCase(repo)

    input_data = LoginInput(identifier="invalidUser", password="123456")

    with pytest.raises(ValueError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "invalid_credentials"


def test_wrong_password(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = LoginUserUseCase(repo)
    input_data = LoginInput(identifier="JhonDoe", password="wrong_password")

    with pytest.raises(ValueError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "invalid_credentials"


def test_inactive_user(repo, make_user):
    user = make_user(is_active=False)
    repo.create(user)

    use_case = LoginUserUseCase(repo)
    input_data = LoginInput(identifier="JhonDoe", password="123456")

    with pytest.raises(ValueError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "inactive_user"
