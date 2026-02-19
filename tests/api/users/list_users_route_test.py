from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.core.security import jwt_service
from app.main import app


client = TestClient(app)


def test_list_users_default_success(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, is_active=True, username="Admin")

    user1 = make_user(is_admin=True, is_active=True, username="Daniela")
    user2 = make_user(is_admin=False, is_active=False, username="Carla")
    user3 = make_user(is_admin=True, is_active=False, username="Bernard")
    user4 = make_user(is_admin=False, is_active=True, username="Adonis")

    users_repo.create(admin)

    users_repo.create(user1)
    users_repo.create(user2)
    users_repo.create(user3)
    users_repo.create(user4)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    name_of_the_first = response.json()["users"][0]["username"]
    assert response.status_code == 200
    assert name_of_the_first == "Admin"

    app.dependency_overrides = {}


def test_list_users_custom_queries_success(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, is_active=True)

    user1 = make_user(is_admin=True, is_active=True, username="Daniela")
    user2 = make_user(is_admin=False, is_active=False, username="Carla")
    user3 = make_user(is_admin=True, is_active=False, username="Bernard")
    user4 = make_user(is_admin=False, is_active=True, username="Adonis")
    user5 = make_user(is_admin=False, is_active=False, username="William")

    users_repo.create(admin)

    users_repo.create(user1)
    users_repo.create(user2)
    users_repo.create(user3)
    users_repo.create(user4)
    users_repo.create(user5)

    token = make_token(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get(
        "/users?is_active=false&direction=desc",
        headers={"Authorization": f"Bearer {token}"},
    )

    name_of_the_first_non_admin = response.json()["users"][1]["username"]
    assert response.status_code == 200
    assert name_of_the_first_non_admin == "William"

    app.dependency_overrides = {}


def test_not_admin(users_repo, make_user, make_token):
    not_admin = make_user(is_admin=False, is_active=True)

    user1 = make_user(is_admin=True, is_active=True, username="Daniela")

    users_repo.create(not_admin)

    users_repo.create(user1)

    token = make_token(not_admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    app.dependency_overrides = {}


def test_inactive_admin(users_repo, make_user, make_token):
    inactive_admin = make_user(is_admin=True, is_active=False)

    user1 = make_user(is_admin=True, is_active=True, username="Daniela")

    users_repo.create(inactive_admin)

    users_repo.create(user1)

    token = make_token(inactive_admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_list_users(users_repo, make_user, make_token):
    user = make_user()
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_token_type_list_users(users_repo, make_user, make_token):
    admin = make_user(is_admin=True, is_active=True)
    users_repo.create(admin)
    token = make_token(admin, token_type="refresh")

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_missing_authorization_header(users_repo):
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get(
        "/users",
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]

    app.dependency_overrides = {}


def test_missing_bearer_prefix(users_repo):
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get("/users", headers={"Authorization": "Token 123"})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_jwt_format(users_repo):
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get(
        "/users",
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_token_sub(users_repo):
    app.dependency_overrides[get_users_repository] = lambda: users_repo

    token = jwt_service.create(subject="not-a-uuid", minutes=60, token_type="access")

    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_list_users_negative_page(users_repo, make_user):
    admin = make_user(is_admin=True, is_active=True)
    users_repo.create(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get("/users?page=-1")

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_users_invalid_limit(users_repo, make_user):
    admin = make_user(is_admin=True, is_active=True)
    users_repo.create(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get("/users?limit=0")

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_users_invalid_order_by(users_repo, make_user):
    admin = make_user(is_admin=True, is_active=True)
    users_repo.create(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get("/users?order_by=invalid_field")

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_users_invalid_direction(users_repo, make_user):
    admin = make_user(is_admin=True, is_active=True)
    users_repo.create(admin)

    app.dependency_overrides[get_users_repository] = lambda: users_repo

    response = client.get("/users?direction=sideways")

    assert response.status_code == 422

    app.dependency_overrides = {}
