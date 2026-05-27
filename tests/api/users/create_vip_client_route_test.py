from datetime import datetime, timedelta, timezone

from app.api.dependencies.events import get_integration_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.types.audit_actor_type import AuditActorType
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_create_vip_client_successful(
    write_uow, read_uow, make_user, make_token, fake_integration_event_bus
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "email": "jhon@doe.com",
        "phone": "11912345678",
        "client_code": "JHON-AZUL",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is not None
    assert response.status_code == 201

    assert response.json()["message"] == "VIP Client created"

    app.dependency_overrides = {}


def test_create_vip_client_successful_makes_log(
    write_uow, read_uow, make_user, make_token, fake_integration_event_bus
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "email": "jhon@doe.com",
        "phone": "11912345678",
        "client_code": "JHON-AZUL",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    log = logs[0]

    assert log is not None
    assert log.entity_name == "users"
    assert log.entity_id == vip_client_in_repo.id
    assert log.action == "create vip client"
    assert log.actor_id == admin.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {
        "initial_state": {
            "first_name": vip_client_in_repo.first_name,
            "last_name": vip_client_in_repo.last_name,
            "email": vip_client_in_repo.email,
            "phone": vip_client_in_repo.phone,
            "client_code": vip_client_in_repo.client_code,
        }
    }
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)

    app.dependency_overrides = {}


def test_vip_client_email_taken(
    write_uow, read_uow, make_user, make_token, make_vip_client, fake_integration_event_bus
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client(
        first_name="Jhon",
        last_name="Doe",
        email="jhon@doe.com",
        phone="71999999999",
        client_code="JHON-AZUL",
    )
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {
        "first_name": "Other",
        "last_name": "Name",
        "email": "jhon@doe.com",
        "phone": "11912345678",
        "client_code": "JHON-RED",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is not None
    assert (
        vip_client_in_repo.client_code.value == "JHON-AZUL"
    )  # code on payload is JHON-RED
    assert response.status_code == 409

    assert response.json()["detail"] == "email_already_taken"

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_vip_client_phone_taken(
    write_uow, read_uow, make_user, make_token, make_vip_client, fake_integration_event_bus
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client(
        first_name="Jhon",
        last_name="Doe",
        email="jhon@doe.com",
        phone="71999999999",
        client_code="JHON-AZUL",
    )
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {
        "first_name": "Other",
        "last_name": "Name",
        "email": "other@doe.com",
        "phone": "71999999999",
        "client_code": "JHON-RED",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_phone("71999999999")
    assert vip_client_in_repo is not None
    assert (
        vip_client_in_repo.client_code.value == "JHON-AZUL"
    )  # code on payload is JHON-RED
    assert response.status_code == 409

    assert response.json()["detail"] == "phone_already_taken"

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_vip_client_code_taken(
    write_uow, read_uow, make_user, make_token, make_vip_client, fake_integration_event_bus
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client(
        first_name="Jhon",
        last_name="Doe",
        email="jhon@doe.com",
        phone="71999999999",
        client_code="JHON-AZUL",
    )
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {
        "first_name": "Other",
        "last_name": "Name",
        "email": "other@doe.com",
        "phone": "71912345678",
        "client_code": "JHON-AZUL",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_client_code("JHON-AZUL")
    assert vip_client_in_repo is not None
    assert (
        vip_client_in_repo.email == "jhon@doe.com"
    )  # email on payload is other@doe.com
    assert response.status_code == 409

    assert (
        response.json()["detail"] == "client_code_already_taken_please_generate_another"
    )

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_invalid_email_triggers_validation_error(
    write_uow, read_uow, make_user, make_token, fake_integration_event_bus
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "email": "this_is_not_an_email",
        "phone": "11912345678",
        "client_code": "JHON-AZUL",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None
    assert response.status_code == 422

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_not_admin_create_vip_client(
    write_uow, read_uow, make_user, make_token, fake_integration_event_bus
):
    admin = make_user(is_admin=False, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "email": "jhon@doe.com",
        "phone": "11912345678",
        "client_code": "JHON-AZUL",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_inactive_admin_create_vip_client(
    write_uow, read_uow, make_user, make_token, fake_integration_event_bus
):
    admin = make_user(is_admin=True, is_active=False, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "email": "jhon@doe.com",
        "phone": "11912345678",
        "client_code": "JHON-AZUL",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_non_existent_user_create_vip_client(
    write_uow, read_uow, make_user, make_token, fake_integration_event_bus
):
    admin = make_user(is_admin=True, email="admin@admin.com")

    token = make_token(admin)

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "email": "jhon@doe.com",
        "phone": "11912345678",
        "client_code": "JHON-AZUL",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}


def test_wrong_token_type_create_vip_client(
    write_uow, read_uow, make_user, make_token, fake_integration_event_bus
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin, token_type="refresh")

    payload = {
        "first_name": "Jhon",
        "last_name": "Doe",
        "email": "jhon@doe.com",
        "phone": "11912345678",
        "client_code": "JHON-AZUL",
    }

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []

    app.dependency_overrides = {}
