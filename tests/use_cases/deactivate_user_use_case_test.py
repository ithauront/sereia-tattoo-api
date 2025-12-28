from uuid import uuid4

import pytest
from app.domain.users.use_cases.DTO.user_status_dto import DeactivateUserInput
from app.domain.users.use_cases.deactivate_user import DeactivateUserUseCase


def test_deactivate_user_success(repo, make_user):
    admin = make_user(
        is_active=True, is_admin=True
    )  # admin is verify in route but I prefer to explicit admin here
    user = make_user(is_active=True)
    repo.create(admin)
    repo.create(user)

    use_case = DeactivateUserUseCase(repo)
    input_data = DeactivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_active is False


def test_cannot_deactivate_yourself(repo, make_user):
    admin1 = make_user(is_admin=True)
    admin2 = make_user(is_admin=True)  # 2 admins to not mistake with last admin rule.

    repo.create(admin1)
    repo.create(admin2)

    use_case = DeactivateUserUseCase(repo)
    input_data = DeactivateUserInput(user_id=admin1.id, actor_id=admin1.id)

    with pytest.raises(ValueError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "cannot_deactivate_yourself"


def test_last_active_admin_cannot_be_deactivated(repo, make_user):
    inactive_admin = make_user(
        is_admin=True, is_active=False
    )  # actor active verification is made in controller
    last_active_admin = make_user(is_admin=True)
    repo.create(inactive_admin)
    repo.create(last_active_admin)

    use_case = DeactivateUserUseCase(repo)
    input_data = DeactivateUserInput(
        user_id=last_active_admin.id, actor_id=inactive_admin.id
    )

    with pytest.raises(ValueError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "last_admin_cannot_be_deactivated"


def test_user_not_found_to_deactivate(repo, make_user):
    admin = make_user(is_active=True, is_admin=True)
    not_user_id = uuid4()
    repo.create(admin)

    use_case = DeactivateUserUseCase(repo)
    input_data = DeactivateUserInput(user_id=not_user_id, actor_id=admin.id)

    with pytest.raises(ValueError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "user_not_found"


def test_user_already_inactive(repo, make_user):
    admin = make_user(is_active=True, is_admin=True)
    user = make_user(is_active=False)
    repo.create(admin)
    repo.create(user)

    use_case = DeactivateUserUseCase(repo)
    input_data = DeactivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_active is False
