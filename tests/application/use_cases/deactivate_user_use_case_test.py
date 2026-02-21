from uuid import uuid4
import pytest
from app.application.studio.use_cases.DTO.user_status_dto import DeactivateUserInput
from app.application.studio.use_cases.users_use_cases.deactivate_user import (
    DeactivateUserUseCase,
)
from app.core.exceptions.users import (
    CannotDeactivateYourselfError,
    LastAdminCannotBeDeactivatedError,
    UserNotFoundError,
)


def test_deactivate_user_success(users_repo, make_user):
    admin = make_user(
        is_active=True, is_admin=True, access_token_version=0, refresh_token_version=0
    )  # admin is verify in route but I prefer to explicit admin here
    user = make_user(is_active=True, has_activated_once=True)
    users_repo.create(admin)
    users_repo.create(user)

    use_case = DeactivateUserUseCase(users_repo)
    input_data = DeactivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_active is False
    assert user.has_activated_once is True
    assert user.access_token_version == 1
    assert user.refresh_token_version == 1


def test_cannot_deactivate_yourself(users_repo, make_user):
    admin1 = make_user(is_admin=True, access_token_version=0, refresh_token_version=0)
    admin2 = make_user(is_admin=True)  # 2 admins to not mistake with last admin rule.

    users_repo.create(admin1)
    users_repo.create(admin2)

    use_case = DeactivateUserUseCase(users_repo)
    input_data = DeactivateUserInput(user_id=admin1.id, actor_id=admin1.id)

    with pytest.raises(CannotDeactivateYourselfError):
        use_case.execute(input_data)

    assert admin1.access_token_version == 0
    assert admin1.refresh_token_version == 0


def test_last_active_admin_cannot_be_deactivated(users_repo, make_user):
    inactive_admin = make_user(
        is_admin=True, is_active=False
    )  # actor active verification is made in controller
    last_active_admin = make_user(is_admin=True)
    users_repo.create(inactive_admin)
    users_repo.create(last_active_admin)

    use_case = DeactivateUserUseCase(users_repo)
    input_data = DeactivateUserInput(
        user_id=last_active_admin.id, actor_id=inactive_admin.id
    )

    with pytest.raises(LastAdminCannotBeDeactivatedError):
        use_case.execute(input_data)


def test_user_not_found_to_deactivate(users_repo, make_user):
    admin = make_user(is_active=True, is_admin=True)
    not_user_id = uuid4()
    users_repo.create(admin)

    use_case = DeactivateUserUseCase(users_repo)
    input_data = DeactivateUserInput(user_id=not_user_id, actor_id=admin.id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)


def test_user_already_inactive(users_repo, make_user):
    admin = make_user(is_active=True, is_admin=True)
    user = make_user(is_active=False)
    users_repo.create(admin)
    users_repo.create(user)

    use_case = DeactivateUserUseCase(users_repo)
    input_data = DeactivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_active is False
