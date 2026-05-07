from datetime import timedelta, timezone, datetime

from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.types.audit_actor_type import AuditActorType
from app.main import app

client = TestClient(app)


def test_demote_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    write_uow.users.create(admin)
    write_uow.users.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/{user.id}/demote",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.is_admin is False

    app.dependency_overrides = {}


def test_demote_user_create_log(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    write_uow.users.create(admin)
    write_uow.users.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    client.patch(
        f"/users/{user.id}/demote",
        headers={"Authorization": f"Bearer {token}"},
    )

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")

    log = logs[0]

    assert log.entity_name == "users"
    assert log.entity_id == user.id
    assert log.action == "demote user from admin"
    assert log.actor_id == admin.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {
        "is_admin": {
            "from": True,
            "to": False,
        }
    }
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)

    app.dependency_overrides = {}


def test_demote_nonexistent_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    write_uow.users.create(admin)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/{user.id}/demote",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "user_not_found"
    assert user.is_admin is True

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_route_cannot_demote_yourself(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/{admin.id}/demote",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "cannot_demote_yourself"

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_not_admin_demote_user(write_uow, read_uow, make_user, make_token):
    not_admin = make_user(is_admin=False)
    user = make_user(is_admin=True)

    write_uow.users.create(not_admin)
    write_uow.users.create(user)

    token = make_token(not_admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/{user.id}/demote",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert user.is_admin is True

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_inactive_admin_demote_user(write_uow, read_uow, make_user, make_token):
    inactive_admin = make_user(is_admin=True, is_active=False)
    user = make_user(is_admin=True)

    write_uow.users.create(inactive_admin)
    write_uow.users.create(user)

    token = make_token(inactive_admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/{user.id}/demote",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"
    assert user.is_admin is True

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_nonexistent_user_demote_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    user = make_user(is_admin=True)

    write_uow.users.create(user)

    token = make_token(admin)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/users/{user.id}/demote",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert user.is_admin is True

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}
