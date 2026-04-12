from fastapi.testclient import TestClient

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.main import app


client = TestClient(app)


def test_get_vip_client(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )

    write_uow.client_credit_entries.create(entry)

    token = make_token(admin)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/vip-clients/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    response_vip_client = data["vip_client"]
    response_balance = data["balance"]

    assert response_vip_client["first_name"] == vip_client.first_name
    assert response_vip_client["client_code"] == vip_client.client_code.value
    assert response_balance == 10

    assert "id" in response_vip_client
    assert "first_name" in response_vip_client
    assert "last_name" in response_vip_client
    assert "email" in response_vip_client
    assert "phone" in response_vip_client
    assert "client_code" in response_vip_client
    assert "created_at" in response_vip_client
    assert "updated_at" in response_vip_client

    app.dependency_overrides = {}


def test_user_get_vip_client_success(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    user = make_user(is_admin=False, is_active=True)
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )

    write_uow.client_credit_entries.create(entry)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/vip-clients/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    response_vip_client = data["vip_client"]
    response_balance = data["balance"]

    assert response_vip_client["first_name"] == vip_client.first_name
    assert response_vip_client["client_code"] == vip_client.client_code.value
    assert response_balance == 10

    app.dependency_overrides = {}


def test_get_vip_client_without_credit(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    # we dont add credit for this test

    token = make_token(admin)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/vip-clients/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    response_vip_client = data["vip_client"]
    response_balance = data["balance"]

    assert response_vip_client["first_name"] == vip_client.first_name
    assert response_vip_client["client_code"] == vip_client.client_code.value
    assert response_balance == 0

    assert "id" in response_vip_client
    assert "first_name" in response_vip_client
    assert "last_name" in response_vip_client
    assert "email" in response_vip_client
    assert "phone" in response_vip_client
    assert "client_code" in response_vip_client
    assert "created_at" in response_vip_client
    assert "updated_at" in response_vip_client

    app.dependency_overrides = {}


def test_get_vip_client_not_found(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    # we do not persist vip_client for this test

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )

    write_uow.client_credit_entries.create(entry)

    token = make_token(admin)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/vip-clients/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "vip_client_not_found"

    app.dependency_overrides = {}


def test_inactive_user_cannot_get_vip_client(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    inactive_user = make_user(is_admin=False, is_active=False)
    write_uow.users.create(inactive_user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )

    write_uow.client_credit_entries.create(entry)

    token = make_token(inactive_user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/vip-clients/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403

    data = response.json()
    assert data["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_cannot_get_vip_client(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    inactive_user = make_user(is_admin=True, is_active=True)
    # we do not persist user for this test

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )

    write_uow.client_credit_entries.create(entry)

    token = make_token(inactive_user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/vip-clients/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401

    data = response.json()
    assert data["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_get_invalid_vip_client_uuid(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        vip_client_id=vip_client.id,
    )

    write_uow.client_credit_entries.create(entry)

    token = make_token(admin)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients/invalid_uuid",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}
