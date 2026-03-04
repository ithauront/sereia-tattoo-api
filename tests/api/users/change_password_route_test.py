from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.main import app
from app.core.security.passwords import verify_password

client = TestClient(app)


def test_change_password_success(write_uow, read_uow, make_user, make_token):
    user = make_user()
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"old_password": "123456", "new_password": "StrongPassword1"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    assert verify_password("StrongPassword1", user.hashed_password)

    app.dependency_overrides = {}


def test_change_password_invalid_old_password(
    write_uow, read_uow, make_user, make_token
):
    user = make_user()
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"old_password": "wrong_password", "new_password": "StrongPassword1"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert verify_password("123456", user.hashed_password)

    app.dependency_overrides = {}


def test_inactive_user_change_password(write_uow, read_uow, make_user, make_token):
    user = make_user(is_active=False)
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_change_password(write_uow, read_uow, make_user, make_token):
    user = make_user()
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_token_type(write_uow, read_uow, make_user, make_token):
    user = make_user()
    write_uow.users.create(user)
    token = make_token(user, token_type="refresh")

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"old_password": "123456", "new_password": "abcdef"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_payload_types(write_uow, read_uow, make_user, make_token):
    user = make_user()
    write_uow.users.create(user)

    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"old_password": 123, "new_password": "abcdef"}

    response = client.patch(
        "/me/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
