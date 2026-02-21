import pytest
from uuid import uuid4
from app.application.studio.use_cases.DTO.get_users_dto import GetUserInput
from app.application.studio.use_cases.DTO.user_output_dto import UserOutput
from app.application.studio.use_cases.users_use_cases.get_user import GetUserUseCase
from app.core.exceptions.users import UserNotFoundError


def test_get_user_success(users_repo, make_user):
    user = make_user()
    users_repo.create(user)

    use_case = GetUserUseCase(users_repo)
    dto = GetUserInput(user_id=user.id)

    result = use_case.execute(dto)

    assert result is not None
    assert result.id == user.id
    assert result.username == "JhonDoe"
    assert not hasattr(result, "hashed_password")
    assert not isinstance(result, list)
    assert isinstance(result, UserOutput)


def test_user_not_found(users_repo):
    use_case = GetUserUseCase(users_repo)
    fake_id = uuid4()
    dto = GetUserInput(user_id=fake_id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(dto)
