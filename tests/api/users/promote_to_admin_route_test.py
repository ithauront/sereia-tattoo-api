from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.security import jwt_service
from app.main import app


client = TestClient(app)


def test_promote_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=False)

    write_uow.users.create(admin)
    write_uow.users.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_promote_nonexistent_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=False)

    write_uow.users.create(admin)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_promote_admin_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    write_uow.users.create(admin)
    write_uow.users.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.is_admin is True

    app.dependency_overrides = {}


def test_not_admin_promote_user(write_uow, read_uow, make_user, make_token):
    not_admin = make_user(is_admin=False)
    user = make_user(is_admin=False)

    write_uow.users.create(not_admin)
    write_uow.users.create(user)

    token = make_token(not_admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_inactive_admin_promote_user(write_uow, read_uow, make_user, make_token):
    inactive_admin = make_user(is_admin=True, is_active=False)
    user = make_user(is_admin=False)

    write_uow.users.create(inactive_admin)
    write_uow.users.create(user)

    token = make_token(inactive_admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_nonexistent_user_promote_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=False)

    write_uow.users.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_wrong_token_type_promote_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=False)

    write_uow.users.create(admin)
    write_uow.users.create(user)

    token = make_token(admin, token_type="refresh")

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_missing_authorization_header(write_uow, read_uow, make_user):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=False)

    write_uow.users.create(admin)
    write_uow.users.create(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(f"/users/promote/{user.id}")

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_missing_bearer_prefix(write_uow, make_user, read_uow, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=False)

    write_uow.users.create(admin)
    write_uow.users.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f" {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_invalid_jwt_format(write_uow, read_uow, make_user):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=False)

    write_uow.users.create(admin)
    write_uow.users.create(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_invalid_token_sub(write_uow, read_uow, make_user):
    user = make_user(is_active=False)

    write_uow.users.create(user)

    token = jwt_service.create(subject="not-a-uuid", minutes=60, token_type="access")

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/promote/{user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is False

    app.dependency_overrides = {}
