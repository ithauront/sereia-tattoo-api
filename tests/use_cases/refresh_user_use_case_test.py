from uuid import uuid4
import pytest
from app.core.exceptions.security import TokenError
from app.core.exceptions.users import AuthenticationFailedError
from app.domain.users.use_cases.DTO.login_dto import RefreshInput
from app.domain.users.use_cases.refresh_user import RefreshUserUseCase


def test_refresh_user(users_repo, make_user, refresh_token_service, access_token_service):
    user = make_user(access_token_version=1, refresh_token_version=0)
    users_repo.create(user)

    use_case = RefreshUserUseCase(users_repo, refresh_token_service, access_token_service)
    refresh_token = refresh_token_service.create(user_id=str(user.id), version=0)
    refresh_input = RefreshInput(refresh_token=refresh_token)
    result = use_case.execute(refresh_input)

    assert result.access_token is not None
    assert result.refresh_token is not None
    assert len(result.access_token) > 10
    assert len(result.refresh_token) > 10
    assert refresh_token != result.refresh_token
    saved = users_repo.find_by_id(user.id)
    assert saved.access_token_version == 1
    assert saved.refresh_token_version == 0


def test_refresh_user_wrong_token_version(
    users_repo, make_user, refresh_token_service, access_token_service
):
    user = make_user(refresh_token_version=0)
    users_repo.create(user)

    use_case = RefreshUserUseCase(users_repo, refresh_token_service, access_token_service)
    refresh_token = refresh_token_service.create(user_id=str(user.id), version=1)
    refresh_input = RefreshInput(refresh_token=refresh_token)

    with pytest.raises(TokenError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "token_revoked"


def test_refresh_after_logout(
    users_repo, make_user, refresh_token_service, access_token_service
):
    user = make_user(refresh_token_version=0)
    users_repo.create(user)

    stolen = refresh_token_service.create(user_id=str(user.id), version=0)

    # incrementamos o refresh para simular um logout
    user.refresh_token_version = 1
    users_repo.update(user)

    use_case = RefreshUserUseCase(users_repo, refresh_token_service, access_token_service)

    with pytest.raises(TokenError) as exception:
        use_case.execute(RefreshInput(refresh_token=stolen))

    assert str(exception.value) == "token_revoked"


def test_wrong_token(users_repo, make_user, refresh_token_service, access_token_service):
    user = make_user()
    users_repo.create(user)
    use_case = RefreshUserUseCase(users_repo, refresh_token_service, access_token_service)
    refresh_input = RefreshInput(refresh_token="wrong_token")

    with pytest.raises(TokenError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "invalid_token"


def test_wrong_token_type(users_repo, make_user, refresh_token_service, access_token_service):
    user = make_user()
    users_repo.create(user)

    use_case = RefreshUserUseCase(users_repo, refresh_token_service, access_token_service)
    access_token = access_token_service.create(user_id=str(user.id), version=0)
    refresh_input = RefreshInput(refresh_token=access_token)

    with pytest.raises(TokenError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "invalid_token"


def test_expired_token(users_repo, make_user, refresh_token_service, access_token_service):
    user = make_user()
    users_repo.create(user)

    use_case = RefreshUserUseCase(users_repo, refresh_token_service, access_token_service)
    refresh_token = refresh_token_service.jwt.create(
        subject=str(user.id), minutes=-1, token_type="refresh", extra_claims={"ver": 0}
    )

    refresh_input = RefreshInput(refresh_token=refresh_token)

    with pytest.raises(TokenError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "invalid_token"


def test_wrong_user(users_repo, refresh_token_service, access_token_service):
    use_case = RefreshUserUseCase(users_repo, refresh_token_service, access_token_service)
    fake_id = uuid4()
    refresh_token = refresh_token_service.create(user_id=str(fake_id), version=0)
    refresh_input = RefreshInput(refresh_token=refresh_token)

    with pytest.raises(AuthenticationFailedError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "user_not_found_or_inactive"
