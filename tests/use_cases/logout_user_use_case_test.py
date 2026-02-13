from uuid import uuid4

import pytest
from app.core.exceptions.users import UserNotFoundError
from app.domain.users.use_cases.DTO.login_dto import LogoutInput
from app.domain.users.use_cases.logout_user import LogoutUserUseCase


def test_logout_success(repo, make_user):
    user = make_user(
        access_token_version=0, refresh_token_version=0, email="jhon@doe.com"
    )
    repo.create(user)

    old_updated_at = user.updated_at

    use_case = LogoutUserUseCase(repo)
    input_data = LogoutInput(user_id=user.id)

    use_case.execute(input_data)

    user_in_repo = repo.find_by_id(user.id)

    assert user_in_repo.access_token_version == 1
    assert user_in_repo.refresh_token_version == 1
    assert old_updated_at < user_in_repo.updated_at
    assert user_in_repo.email == "jhon@doe.com"


def test_logout_user_not_found(repo):
    fake_user_id = uuid4()

    use_case = LogoutUserUseCase(repo)
    input_data = LogoutInput(user_id=fake_user_id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)


def test_logout_twice_bumps_tokens_twice(repo, make_user):
    # isso dificilmente vai acontecer, mas testamos para saber que se ocorrer ele não quebra nada
    user = make_user()
    repo.create(user)

    use_case = LogoutUserUseCase(repo)
    input_data = LogoutInput(user_id=user.id)
    use_case.execute(input_data)
    use_case.execute(input_data)

    user_in_repo = repo.find_by_id(user.id)

    assert user_in_repo.access_token_version == 2
    assert user_in_repo.refresh_token_version == 2
