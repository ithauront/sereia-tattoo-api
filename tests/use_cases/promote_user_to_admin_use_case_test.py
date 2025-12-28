from uuid import uuid4

import pytest
from app.domain.users.use_cases.DTO.user_status_dto import (
    PromoteUserInput,
)
from app.domain.users.use_cases.promote_user_to_admin import PromoteUserToAdminUseCase


def test_promote_user_success(repo, make_user):
    user = make_user(is_active=True, is_admin=False)

    repo.create(user)

    use_case = PromoteUserToAdminUseCase(repo)
    input_data = PromoteUserInput(user_id=user.id)

    use_case.execute(input_data)

    assert user.is_admin is True


def test_user_not_found_to_promote(repo):
    not_user_id = uuid4()

    use_case = PromoteUserToAdminUseCase(repo)
    input_data = PromoteUserInput(user_id=not_user_id)

    with pytest.raises(ValueError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "user_not_found"


def test_user_already_axmin(repo, make_user):
    user = make_user(is_active=True, is_admin=True)

    repo.create(user)

    use_case = PromoteUserToAdminUseCase(repo)
    input_data = PromoteUserInput(user_id=user.id)

    use_case.execute(input_data)

    assert user.is_admin is True
