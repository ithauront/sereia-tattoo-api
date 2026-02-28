import pytest
from uuid import uuid4
from app.application.studio.use_cases.DTO.get_users_dto import GetUserInput
from app.application.studio.use_cases.DTO.user_output_dto import UserOutput
from app.application.studio.use_cases.users_use_cases.get_user import GetUserUseCase
from app.core.exceptions.users import UserNotFoundError


def test_get_user_success(read_uow, write_uow, make_user):
    user = make_user()
    write_uow.users.create(user)

    use_case = GetUserUseCase(read_uow)
    dto = GetUserInput(user_id=user.id)

    result = use_case.execute(dto)

    assert result is not None
    assert result.id == user.id
    assert result.username == "JhonDoe"
    assert not hasattr(result, "hashed_password")
    assert not isinstance(result, list)
    assert isinstance(result, UserOutput)


def test_user_not_found(read_uow):
    use_case = GetUserUseCase(read_uow)
    fake_id = uuid4()
    dto = GetUserInput(user_id=fake_id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(dto)
