from uuid import uuid4

import pytest
from app.core.exceptions.users import UserNotFoundError
from app.domain.users.use_cases.DTO.user_status_dto import (
    PromoteUserInput,
)
from app.domain.users.use_cases.promote_user_to_admin import PromoteUserToAdminUseCase


def test_promote_user_success(users_repo, make_user):
    user = make_user(is_active=True, is_admin=False)

    users_repo.create(user)

    use_case = PromoteUserToAdminUseCase(users_repo)
    input_data = PromoteUserInput(user_id=user.id)

    use_case.execute(input_data)

    assert user.is_admin is True


def test_user_not_found_to_promote(users_repo):
    not_user_id = uuid4()

    use_case = PromoteUserToAdminUseCase(users_repo)
    input_data = PromoteUserInput(user_id=not_user_id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)


def test_user_already_axmin(users_repo, make_user):
    user = make_user(is_active=True, is_admin=True)

    users_repo.create(user)

    use_case = PromoteUserToAdminUseCase(users_repo)
    input_data = PromoteUserInput(user_id=user.id)

    use_case.execute(input_data)

    assert user.is_admin is True
