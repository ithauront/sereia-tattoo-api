from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.types.audit_actor_type import AuditActorType
from app.main import app

client = TestClient(app)


def test_change_email_success(write_uow, read_uow, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "123456", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.email == "new@email.com"

    app.dependency_overrides = {}


def test_change_email_create_log(write_uow, read_uow, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)
    old_email = user.email

    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "123456", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    log = logs[0]

    assert log.entity_name == "users"
    assert log.entity_id == user.id
    assert log.action == "change user email"
    assert log.actor_id == user.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {
        "email": {
            "from": old_email,
            "to": "new@email.com",
        }
    }
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)

    app.dependency_overrides = {}


def test_change_email_same_email_idempotent(write_uow, read_uow, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "123456", "new_email": "jhon@doe.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.email == "jhon@doe.com"

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert logs == []


def test_change_email_normalization(write_uow, read_uow, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "123456", "new_email": " New@Email.COM "}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.email == "new@email.com"

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert len(logs) == 1

    app.dependency_overrides = {}


def test_change_email_wrong_password(write_uow, read_uow, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "wrong_password", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "invalid_credentials"
    assert user.email == "jhon@doe.com"

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert logs == []

    app.dependency_overrides = {}


def test_change_email_already_taken(write_uow, read_uow, make_user, make_token):
    user1 = make_user(email="jhon@doe.com")
    write_uow.users.create(user1)
    token = make_token(user1)
    user2 = make_user(email="already@taken.com")
    write_uow.users.create(user2)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "123456", "new_email": "already@taken.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "email_chosen_is_already_taken"
    assert user1.email == "jhon@doe.com"

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_inactive_user_change_email(write_uow, read_uow, make_user, make_token):
    user = make_user(is_active=False, email="jhon@doe.com")
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "123456", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert logs == []

    app.dependency_overrides = {}


def test_not_user_change_email(write_uow, read_uow, make_user, make_token):
    user = make_user()
    token = make_token(user)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"password": "123456", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert logs == []

    app.dependency_overrides = {}
