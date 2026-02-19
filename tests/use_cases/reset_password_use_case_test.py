from uuid import uuid4

import pytest
from app.core.exceptions.users import (
    InvalidPasswordTokenError,
    UserInactiveError,
    UserNotFoundError,
)
from app.domain.users.use_cases.DTO.password_dto import ResetPasswordInput
from app.domain.users.use_cases.reset_password import ResetPasswordUseCase
from app.core.security.passwords import verify_password


def test_reset_password_success(users_repo, make_user):
    user = make_user(
        password_token_version=0, access_token_version=0, refresh_token_version=0
    )
    users_repo.create(user)
    old_hash = user.hashed_password

    use_case = ResetPasswordUseCase(users_repo)

    input_data = ResetPasswordInput(
        password="StrongPassword1", user_id=user.id, password_token_version=0
    )

    use_case.execute(input_data)

    assert old_hash != user.hashed_password
    saved = users_repo.find_by_id(user.id)
    assert verify_password("StrongPassword1", saved.hashed_password)
    assert saved.password_token_version == 1
    assert saved.access_token_version == 1
    assert saved.refresh_token_version == 1


def test_reset_password_wrong_user_id(users_repo, make_user):
    user = make_user(password_token_version=0)
    users_repo.create(user)
    wrong_id = uuid4()

    use_case = ResetPasswordUseCase(users_repo)

    input_data = ResetPasswordInput(
        password="StrongPassword1", user_id=wrong_id, password_token_version=0
    )

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)

    saved = users_repo.find_by_id(user.id)
    assert saved.password_token_version == 0


def test_reset_password_wrong_token_version(users_repo, make_user):
    user = make_user(password_token_version=1)
    users_repo.create(user)

    use_case = ResetPasswordUseCase(users_repo)

    input_data = ResetPasswordInput(
        password="StrongPassword1", user_id=user.id, password_token_version=0
    )

    with pytest.raises(InvalidPasswordTokenError):
        use_case.execute(input_data)

    saved = users_repo.find_by_id(user.id)
    assert saved.password_token_version == 1


def test_reset_password_user_inactive(users_repo, make_user):
    user = make_user(password_token_version=0, is_active=False)
    users_repo.create(user)

    use_case = ResetPasswordUseCase(users_repo)

    input_data = ResetPasswordInput(
        password="StrongPassword1", user_id=user.id, password_token_version=0
    )

    with pytest.raises(UserInactiveError):
        use_case.execute(input_data)

    saved = users_repo.find_by_id(user.id)
    assert saved.password_token_version == 0
