from uuid import uuid4
import pytest
from app.application.studio.use_cases.DTO.login_dto import VerifyInput
from app.application.studio.use_cases.users_use_cases.verify_user import (
    VerifyUserUseCase,
)
from app.core.exceptions.security import TokenError


def test_verify_user(read_uow, write_uow, make_user, access_token_service):
    user = make_user()
    write_uow.users.create(user)

    use_case = VerifyUserUseCase(read_uow, access_token_service)
    access_token = access_token_service.create(user_id=str(user.id), version=0)
    input_data = VerifyInput(authorization=f"Bearer {access_token}")
    result = use_case.execute(input_data)

    assert result.valid is True
    assert result.sub == str(user.id)
    assert result.type == "access"


def test_verify_user_wrong_token_version(
    read_uow, write_uow, make_user, access_token_service
):
    user = make_user(access_token_version=0)
    write_uow.users.create(user)

    use_case = VerifyUserUseCase(read_uow, access_token_service)
    access_token = access_token_service.create(user_id=str(user.id), version=1)
    input_data = VerifyInput(authorization=f"Bearer {access_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "token_revoked"


def test_not_bearer_token(read_uow, write_uow, make_user, access_token_service):
    user = make_user()
    write_uow.users.create(user)

    use_case = VerifyUserUseCase(read_uow, access_token_service)
    access_token = access_token_service.create(user_id=str(user.id), version=0)
    input_data = VerifyInput(authorization=f"Not a Bearer {access_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "missing_bearer_token"


def test_invalid_token(read_uow, access_token_service):
    use_case = VerifyUserUseCase(read_uow, access_token_service)
    fake_id = uuid4()
    access_token = access_token_service.create(user_id=str(fake_id), version=0)
    input_data = VerifyInput(authorization=f"Bearer {access_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "invalid_token"


def test_wrong_token_type(
    read_uow, write_uow, make_user, access_token_service, refresh_token_service
):
    user = make_user()
    write_uow.users.create(user)

    use_case = VerifyUserUseCase(read_uow, access_token_service)
    refresh_token = refresh_token_service.create(user_id=str(user.id), version=0)
    input_data = VerifyInput(authorization=f"Bearer {refresh_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "invalid_token"


def test_expired_token(read_uow, write_uow, make_user, access_token_service):
    user = make_user()
    write_uow.users.create(user)

    use_case = VerifyUserUseCase(read_uow, access_token_service)
    access_token = access_token_service.jwt.create(
        subject=str(user.id), minutes=-1, token_type="access", extra_claims={"ver": 0}
    )

    input_data = VerifyInput(authorization=f"Bearer {access_token}")

    with pytest.raises(TokenError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "invalid_token"
