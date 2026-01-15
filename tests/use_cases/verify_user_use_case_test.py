from uuid import uuid4
import pytest
from app.core.config import settings
from app.core.exceptions.security import TokenError
from app.core.security import jwt_service
from app.domain.users.use_cases.DTO.login_dto import VerifyInput
from app.domain.users.use_cases.verify_user import VerifyUserUseCase


def test_verify_user(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = VerifyUserUseCase(repo)
    access_token = jwt_service.create(
        subject=str(user.id),
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )
    input_data = VerifyInput(authorization=f"Bearer {access_token}")
    result = use_case.execute(input_data)

    assert result.valid is True
    assert result.sub == str(user.id)
    assert result.type == "access"


def test_not_bearer_token(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = VerifyUserUseCase(repo)
    access_token = jwt_service.create(
        subject=str(user.id),
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )
    input_data = VerifyInput(authorization=f"Not a Bearer {access_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "missing_bearer_token"


def test_invalid_token(repo):
    use_case = VerifyUserUseCase(repo)
    fake_id = uuid4()
    access_token = jwt_service.create(
        subject=str(fake_id),
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="access",
    )
    input_data = VerifyInput(authorization=f"Bearer {access_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "invalid_token"


def test_wrong_token_type(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = VerifyUserUseCase(repo)
    access_token = jwt_service.create(
        subject=str(user.id),
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        token_type="refresh",
    )
    input_data = VerifyInput(authorization=f"Bearer {access_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "invalid_token"


def test_expired_token(repo, make_user):
    user = make_user()
    repo.create(user)

    use_case = VerifyUserUseCase(repo)
    access_token = jwt_service.create(
        subject=str(user.id),
        minutes=-1,
        token_type="access",
    )

    input_data = VerifyInput(authorization=f"Bearer {access_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "invalid_token"
