from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.types.audit_actor_type import AuditActorType
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


def test_change_password_create_log(write_uow, read_uow, make_user, make_token):
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

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    log = logs[0]

    assert log.entity_name == "users"
    assert log.entity_id == user.id
    assert log.action == "change user password"
    assert log.actor_id == user.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {
        "password": {
            "change": True,
        }
    }
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)

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

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert logs == []

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

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert logs == []

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

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert logs == []

    app.dependency_overrides = {}
