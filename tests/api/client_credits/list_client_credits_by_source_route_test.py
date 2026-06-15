from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.main import app

client = TestClient(app)


def test_list_vip_client_credit_entries_by_admin_source_default(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "entries" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

    assert data["total"] == 10
    assert data["page"] == 1
    assert data["limit"] == 20

    assert len(data["entries"]) == 10
    assert data["entries"][0]["quantity"] == 1

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_by_appointment_source_default(
    write_uow, read_uow, make_user, make_token, make_client_credit_entry, make_completed_appointment
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    appointment = make_completed_appointment()
    write_uow.appointments.create(appointment)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=appointment.id, quantity=i, reason="Créditos referentes a indicação."
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{appointment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "entries" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

    assert data["total"] == 10
    assert data["page"] == 1
    assert data["limit"] == 20

    assert len(data["entries"]) == 10
    assert data["entries"][0]["quantity"] == 1

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_with_params(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
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


def test_list_vip_client_credit_entries_empty_list(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    # we do not create client credit entries for this test

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
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


def test_list_client_credit_entries_active_non_admin_can_access(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)

    user = make_user(is_admin=False, is_active=True)
    write_uow.users.create(user)
    token = make_token(user)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "entries" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

    assert data["total"] == 10
    assert data["page"] == 1
    assert data["limit"] == 20

    assert len(data["entries"]) == 10
    assert data["entries"][0]["quantity"] == 1

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_req_by_non_user(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)

    non_user = make_user(is_admin=False, is_active=True)
    # we do not persist user for this test
    token = make_token(non_user)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_req_by_inactive_admin(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)

    inactive_admin = make_user(is_admin=True, is_active=False)
    write_uow.users.create(inactive_admin)
    token = make_token(inactive_admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_wrong_page_params(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        params={
            "page": -1,
            "limit": 3,
            "direction": "desc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_wrong_limit_params(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        params={
            "page": 1,
            "limit": 0,
            "direction": "desc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_wrong_direction_params(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        params={
            "page": 1,
            "limit": 1,
            "direction": "wrong_direction",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_over_limit_params(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        params={
            "page": 1,
            "limit": 101,
            "direction": "desc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_vip_client_credit_entries_page_over_total_params(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/by-source/{admin.id}",
        params={
            "page": 999,
            "limit": 10,
            "direction": "desc",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "entries" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

    assert len(data["entries"]) == 0
    assert data["entries"] == []

    assert data["total"] == 10

    assert data["page"] == 999

    app.dependency_overrides = {}
