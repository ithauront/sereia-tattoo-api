from datetime import datetime

from fastapi.testclient import TestClient

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.domain.studio.finances.enums.client_credit_source_type import (
    ClientCreditSourceType,
)
from app.main import app


client = TestClient(app)


def test_get_vip_client_credit_entries_by_id_default(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    user = make_user(is_admin=False, is_active=True)
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry_1 = make_client_credit_entry(
        vip_client_id=vip_client.id,
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
    )
    client_credit_entry_2 = make_client_credit_entry(
        vip_client_id=vip_client.id, quantity=20
    )

    write_uow.client_credit_entries.create(client_credit_entry_1)
    write_uow.client_credit_entries.create(client_credit_entry_2)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-id/{client_credit_entry_1.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] != str(client_credit_entry_2.id)
    assert data["id"] == str(client_credit_entry_1.id)

    assert data["vip_client_name"] == "Jhon Doe"
    assert data["admin_name"] is None
    assert data["source_id"] == str(client_credit_entry_1.source_id)
    assert data["related_entry_id"] is None

    assert data["source_type"] == ClientCreditSourceType.INDICATION.value
    assert data["quantity"] == 10
    assert data["reason"] == "Créditos referentes a indicação."
    # indication reason is hardcoded in entity
    assert (
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        == client_credit_entry_1.created_at
    )

    app.dependency_overrides = {}


def test_get_vip_client_credit_entries_not_found(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    user = make_user(is_admin=False, is_active=True)
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
    )

    # for this test we do not persist credit entry

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-id/{client_credit_entry.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    data = response.json()

    assert data["detail"] == "client_credit_entry_not_found"

    app.dependency_overrides = {}


def test_get_credit_entries_vip_client_not_found(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    # if data is not compromised we should never fall to this situation. this is a defensive test
    user = make_user(is_admin=False, is_active=True)
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    # for this test we do not persist vip client

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
    )

    write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-id/{client_credit_entry.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    data = response.json()

    assert data["detail"] == "client_credit_entry_in_not_attached_to_a_vip_client"

    app.dependency_overrides = {}


def test_get_credit_entries_admin_source_not_found(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    # if data is not compromised we should never fall to this situation. this is a defensive test
    admin_1 = make_user(is_admin=True, is_active=True)
    # for this test we do not persist admin that is source_id

    admin_2 = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin_2)
    token = make_token(admin_2)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        source_id=admin_1.id,
    )

    write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-id/{client_credit_entry.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    data = response.json()

    assert data["detail"] == "credit_came_from_an_admin_operation_but_admin_not_found"

    app.dependency_overrides = {}


def test_get_vip_client_credit_entries_by_id_not_user_request(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    user = make_user(is_admin=False, is_active=True)
    # for this test we do not persist user
    token = make_token(user)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry_1 = make_client_credit_entry(
        vip_client_id=vip_client.id,
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
    )
    client_credit_entry_2 = make_client_credit_entry(
        vip_client_id=vip_client.id, quantity=20
    )

    write_uow.client_credit_entries.create(client_credit_entry_1)
    write_uow.client_credit_entries.create(client_credit_entry_2)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-id/{client_credit_entry_1.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_get_vip_client_credit_entries_by_id_inactive_user_request(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    user = make_user(is_admin=False, is_active=False)
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry_1 = make_client_credit_entry(
        vip_client_id=vip_client.id,
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
    )
    client_credit_entry_2 = make_client_credit_entry(
        vip_client_id=vip_client.id, quantity=20
    )

    write_uow.client_credit_entries.create(client_credit_entry_1)
    write_uow.client_credit_entries.create(client_credit_entry_2)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-id/{client_credit_entry_1.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}