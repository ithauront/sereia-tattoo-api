import pytest
from app.core.exceptions.users import AuthenticationFailedError, UserInactiveError
from app.core.security import jwt_service
from app.domain.users.use_cases.DTO.login_dto import LoginInput
from app.domain.users.use_cases.login_user import LoginUserUseCase


def test_login_sucess(users_repo, make_user, access_token_service, refresh_token_service):
    user = make_user(access_token_version=0, refresh_token_version=0)
    users_repo.create(user)

    use_case = LoginUserUseCase(users_repo, access_token_service, refresh_token_service)
    input_data = LoginInput(identifier="JhonDoe", password="123456")

    result = use_case.execute(input_data)

    access_payload = jwt_service.decode(result.access_token)
    refresh_payload = jwt_service.decode(result.refresh_token)

    assert access_payload["ver"] == 0
    assert refresh_payload["ver"] == 0

    assert result.access_token is not None
    assert result.refresh_token is not None
    assert len(result.access_token) > 10
    assert len(result.refresh_token) > 10


def test_user_not_found(users_repo, make_user, access_token_service, refresh_token_service):
    user = make_user()
    users_repo.create(user)

    use_case = LoginUserUseCase(users_repo, access_token_service, refresh_token_service)

    input_data = LoginInput(identifier="invalidUser", password="123456")

    with pytest.raises(AuthenticationFailedError):
        use_case.execute(input_data)


def test_wrong_password(users_repo, make_user, access_token_service, refresh_token_service):
    user = make_user()
    users_repo.create(user)

    use_case = LoginUserUseCase(users_repo, access_token_service, refresh_token_service)
    input_data = LoginInput(identifier="JhonDoe", password="wrong_password")

    with pytest.raises(AuthenticationFailedError):
        use_case.execute(input_data)


def test_inactive_user(users_repo, make_user, access_token_service, refresh_token_service):
    user = make_user(is_active=False)
    users_repo.create(user)

    use_case = LoginUserUseCase(users_repo, access_token_service, refresh_token_service)
    input_data = LoginInput(identifier="JhonDoe", password="123456")

    with pytest.raises(UserInactiveError):
        use_case.execute(input_data)
