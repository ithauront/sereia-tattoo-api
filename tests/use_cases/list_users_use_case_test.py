from pydantic import ValidationError
import pytest
from app.domain.users.use_cases.DTO.get_users_dto import ListUsersInput
from app.domain.users.use_cases.list_users import ListUsersUseCase
from freezegun import freeze_time


def test_list_users_default_success(users_repo, make_user):
    user1 = make_user(is_admin=True, is_active=True, username="Daniela")
    user2 = make_user(is_admin=False, is_active=False, username="Carla")
    user3 = make_user(is_admin=True, is_active=False, username="Bernard")
    user4 = make_user(is_admin=False, is_active=True, username="Adonis")

    users_repo.create(user1)
    users_repo.create(user2)
    users_repo.create(user3)
    users_repo.create(user4)
    use_case = ListUsersUseCase(users_repo)
    input_data = ListUsersInput()

    result = use_case.execute(input_data)

    assert result.users is not None
    assert result.users[0].username == "Bernard"  # sort admins first alphabetical
    assert result.users[1].username == "Daniela"  # sort admins first
    assert result.users[2].username == "Adonis"  # sort alphabetical
    assert result.users[3].username == "Carla"


def test_list_users_descendent_success(users_repo, make_user):
    user1 = make_user(is_admin=True, is_active=True, username="Daniela")
    user2 = make_user(is_admin=False, is_active=False, username="Carla")
    user3 = make_user(is_admin=True, is_active=False, username="Bernard")
    user4 = make_user(is_admin=False, is_active=True, username="Adonis")

    users_repo.create(user1)
    users_repo.create(user2)
    users_repo.create(user3)
    users_repo.create(user4)
    use_case = ListUsersUseCase(users_repo)
    input_data = ListUsersInput(direction="desc")

    result = use_case.execute(input_data)

    assert result.users is not None
    assert (
        result.users[0].username == "Daniela"
    )  # sort admins first alphabetical descendent
    assert result.users[1].username == "Bernard"  # sort admins first
    assert result.users[2].username == "Carla"  # sort alphabetical descendent
    assert result.users[3].username == "Adonis"


def test_list_admins_success(users_repo, make_user):
    user1 = make_user(is_admin=True, is_active=True, username="Daniela")
    user2 = make_user(is_admin=False, is_active=False, username="Carla")
    user3 = make_user(is_admin=True, is_active=False, username="Bernard")
    user4 = make_user(is_admin=False, is_active=True, username="Adonis")

    users_repo.create(user1)
    users_repo.create(user2)
    users_repo.create(user3)
    users_repo.create(user4)
    use_case = ListUsersUseCase(users_repo)
    input_data = ListUsersInput(is_admin=True)

    result = use_case.execute(input_data)

    assert result.users is not None
    assert len(result.users) == 2
    assert result.users[0].username == "Bernard"  # sort alphabetical
    assert result.users[1].username == "Daniela"


def test_list_active_users_success(users_repo, make_user):
    user1 = make_user(is_admin=True, is_active=True, username="Daniela")
    user2 = make_user(is_admin=False, is_active=False, username="Carla")
    user3 = make_user(is_admin=True, is_active=False, username="Bernard")
    user4 = make_user(is_admin=False, is_active=True, username="Adonis")

    users_repo.create(user1)
    users_repo.create(user2)
    users_repo.create(user3)
    users_repo.create(user4)
    use_case = ListUsersUseCase(users_repo)
    input_data = ListUsersInput(is_active=True)

    result = use_case.execute(input_data)

    assert result.users is not None
    assert len(result.users) == 2
    assert result.users[0].username == "Daniela"  # sort alphabetical
    assert result.users[1].username == "Adonis"


def test_list_combine_active_admins_success(users_repo, make_user):
    user1 = make_user(is_admin=True, is_active=True, username="Daniela")
    user2 = make_user(is_admin=False, is_active=False, username="Carla")
    user3 = make_user(is_admin=True, is_active=False, username="Bernard")
    user4 = make_user(is_admin=False, is_active=True, username="Adonis")

    users_repo.create(user1)
    users_repo.create(user2)
    users_repo.create(user3)
    users_repo.create(user4)
    use_case = ListUsersUseCase(users_repo)
    input_data = ListUsersInput(is_active=True, is_admin=True)

    result = use_case.execute(input_data)

    assert result.users is not None
    assert len(result.users) == 1
    assert result.users[0].username == "Daniela"


@freeze_time("2025-01-01")
def test_list_by_created_at_success(users_repo, make_user):
    user1 = make_user(is_admin=True, is_active=True, username="Daniela")
    users_repo.create(user1)

    with freeze_time("2025-01-02"):
        user2 = make_user(is_admin=False, is_active=False, username="Carla")
        users_repo.create(user2)

    with freeze_time("2025-01-03"):
        user3 = make_user(is_admin=True, is_active=False, username="Bernard")
        users_repo.create(user3)

    with freeze_time("2025-01-04"):
        user4 = make_user(is_admin=False, is_active=True, username="Adonis")
        users_repo.create(user4)

    use_case = ListUsersUseCase(users_repo)
    input_data = ListUsersInput(order_by="created_at")

    result = use_case.execute(input_data)

    assert result.users is not None
    assert result.users[0].username == "Daniela"  # sort admins first and created_at
    assert result.users[1].username == "Bernard"  # sort admins first
    assert result.users[2].username == "Carla"  # sort created_at
    assert result.users[3].username == "Adonis"


def test_pagination_and_limit_success(users_repo, make_user):
    for i in range(16):
        letter = chr(ord("a") + i)
        user = make_user(username=f"user{letter}")
        users_repo.create(user)

    use_case = ListUsersUseCase(users_repo)
    input_data = ListUsersInput(page=2, limit=10)

    result = use_case.execute(input_data)

    assert result.users is not None
    assert len(result.users) == 6
    assert result.users[0].username == "userk"  # 11th letter
    assert result.users[-1].username == "userp"  # 16th letter


def test_empty_db(users_repo):

    use_case = ListUsersUseCase(users_repo)
    input_data = ListUsersInput()

    result = use_case.execute(input_data)

    assert result.users == []
    assert len(result.users) == 0


# DTO for listUsersUseCase tests
def test_page_cannot_be_less_than_one(users_repo):
    with pytest.raises(ValidationError):
        ListUsersInput(page=0)


def test_limit_cannot_be_less_than_one():
    with pytest.raises(ValidationError):
        ListUsersInput(limit=0)
