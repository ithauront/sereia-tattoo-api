from uuid import uuid4
import pytest
from app.core.exceptions.security import TokenError
from app.core.exceptions.users import AuthenticationFailedError
from app.domain.users.use_cases.DTO.login_dto import RefreshInput
from app.domain.users.use_cases.refresh_user import RefreshUserUseCase
from app.core.config import settings
from app.core.security import jwt_service


def test_refresh_user(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = RefreshUserUseCase(repo)
    refresh_token = jwt_service.create(
        subject=str(user.id),
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        token_type="refresh",
    )
    refresh_input = RefreshInput(refresh_token=refresh_token)
    result = use_case.execute(refresh_input)

    assert result.access_token is not None
    assert result.refresh_token is not None
    assert len(result.access_token) > 10
    assert len(result.refresh_token) > 10
    assert refresh_token != result.refresh_token


def test_wrong_token(repo, make_user):
    user = make_user()
    repo.create(user)
    use_case = RefreshUserUseCase(repo)
    refresh_input = RefreshInput(refresh_token="wrong_token")

    with pytest.raises(TokenError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "invalid_token"


def test_wrong_token_type(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = RefreshUserUseCase(repo)
    access_token = jwt_service.create(
        subject=str(user.id),
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )
    refresh_input = RefreshInput(refresh_token=access_token)

    with pytest.raises(TokenError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "invalid_token"


def test_expired_token(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = RefreshUserUseCase(repo)
    refresh_token = jwt_service.create(
        subject=str(user.id),
        minutes=-1,
        token_type="refresh",
    )
    refresh_input = RefreshInput(refresh_token=refresh_token)

    with pytest.raises(TokenError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "invalid_token"


def test_wrong_user(repo):
    use_case = RefreshUserUseCase(repo)
    fake_id = uuid4()
    refresh_token = jwt_service.create(
        subject=str(fake_id),
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        token_type="refresh",
    )
    refresh_input = RefreshInput(refresh_token=refresh_token)

    with pytest.raises(AuthenticationFailedError) as exception:
        use_case.execute(refresh_input)

    assert str(exception.value) == "user_not_found_or_inactive"
