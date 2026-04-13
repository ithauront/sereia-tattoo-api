from fastapi.testclient import TestClient

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.main import app


client = TestClient(app)


def test_list_vip_client_credit_entries_by_vip_client_default(
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

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 6):
        client_redit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_redit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "entries" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

    assert data["total"] == 5
    assert data["page"] == 1
    assert data["limit"] == 20

    assert len(data["entries"]) == 5
    assert data["entries"][0]["quantity"] == 1

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_vip_client_with_params(
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

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 11):
        entry = make_client_credit_entry(vip_client_id=vip_client.id, quantity=i)
        write_uow.client_credit_entries.create(entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        params={
            "page": 2,
            "limit": 3,
            "direction": "desc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert data["limit"] == 3
    assert data["total"] == 10

    assert len(data["entries"]) == 3

    assert data["entries"][0]["quantity"] == 7
    assert data["entries"][1]["quantity"] == 6
    assert data["entries"][2]["quantity"] == 5

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_vip_client_empty_list(
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

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    # we do not make credit_entries for this test

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "entries" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20

    assert len(data["entries"]) == 0
    assert data["entries"] == []

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_vip_client_by_admin(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 6):
        client_redit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_redit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_vip_client_by_non_user(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    non_user = make_user(is_admin=True, is_active=True)
    # do not persist user
    token = make_token(non_user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 6):
        client_redit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_redit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_vip_client_by_inactive_user(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    inactive_user = make_user(is_admin=False, is_active=False)
    write_uow.users.create(inactive_user)
    token = make_token(inactive_user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 6):
        client_redit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_redit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_vip_client_wrong_page_param(
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

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 6):
        client_redit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_redit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        params={
            "page": -1,
            "limit": 30,
            "direction": "asc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_vip_client_wrong_limit_param(
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

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 6):
        client_redit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_redit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        params={
            "page": 1,
            "limit": 0,
            "direction": "asc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_vip_client_wrong_direction_param(
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

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 6):
        client_redit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_redit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-client/{vip_client.id}",
        params={
            "page": 1,
            "limit": 3,
            "direction": "wrong_direction",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}
