from uuid import uuid4

import pytest
from app.domain.users.use_cases.DTO.user_status_dto import (
    ActivateUserInput,
)
from app.domain.users.use_cases.activate_user import ActivateUserUseCase


def test_activate_user_success(repo, make_user):
    user = make_user(is_active=False)

    repo.create(user)

    use_case = ActivateUserUseCase(repo)
    input_data = ActivateUserInput(user_id=user.id)

    use_case.execute(input_data)

    assert user.is_active is True


def test_user_not_found_to_activate(repo):
    not_user_id = uuid4()

    use_case = ActivateUserUseCase(repo)
    input_data = ActivateUserInput(user_id=not_user_id)

    with pytest.raises(ValueError) as exception:
        use_case.execute(input_data)

    assert str(exception.value) == "user_not_found"


def test_user_already_active(repo, make_user):
    user = make_user(is_active=True)

    repo.create(user)

    use_case = ActivateUserUseCase(repo)
    input_data = ActivateUserInput(user_id=user.id)

    use_case.execute(input_data)

    assert user.is_active is True
