import pytest
from app.core.exceptions.users import AuthenticationFailedError
from app.core.security.passwords import verify_password
from app.domain.users.use_cases.DTO.password_dto import ChangePasswordInput
from app.domain.users.use_cases.change_password import ChangePasswordUseCase


def test_change_password(users_repo, make_user):
    user = make_user(
        password_token_version=0, access_token_version=0, refresh_token_version=0
    )
    users_repo.create(user)

    use_case = ChangePasswordUseCase(users_repo)
    input_data = ChangePasswordInput(
        old_password="123456", new_password="StrongPassword1"
    )

    old_hash = user.hashed_password

    use_case.execute(input_data, user)

    assert user.hashed_password != old_hash

    assert verify_password("StrongPassword1", user.hashed_password)

    saved = users_repo.find_by_id(user.id)
    assert verify_password("StrongPassword1", saved.hashed_password)
    assert saved.password_token_version == 1
    assert saved.access_token_version == 1
    assert saved.refresh_token_version == 1


def test_wrong_old_password(users_repo, make_user):
    user = make_user(
        password_token_version=0, access_token_version=0, refresh_token_version=0
    )
    users_repo.create(user)

    use_case = ChangePasswordUseCase(users_repo)
    input_data = ChangePasswordInput(
        old_password="wrong_password", new_password="StrongPassword1"
    )

    with pytest.raises(AuthenticationFailedError):
        use_case.execute(input_data, user)

    assert user.password_token_version == 0
    assert user.access_token_version == 0
    assert user.refresh_token_version == 0
