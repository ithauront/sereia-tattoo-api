from fastapi.testclient import TestClient

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.main import app

client = TestClient(app)


def test_add_client_credit_by_admin_default(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"quantity": 10, "reason": "adding credits to test"}

    response = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data == {
        "vip_client": str(vip_client.id),
        "quantity_added": 10,
        "total_credits_before": 0,
        "total_credits_after": 10,
    }

    app.dependency_overrides = {}


def test_add_client_credit_by_admin_create_log(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"quantity": 10, "reason": "adding credits to test"}

    client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    assert len(logs) == 1
    assert logs[0].action == "admin added credits"

    app.dependency_overrides = {}


def test_add_client_credit_by_admin_two_calls(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"quantity": 10, "reason": "adding credits to test"}

    response_1 = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    response_2 = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_1.status_code == 201

    assert response_2.status_code == 201

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )

    assert len(logs) == 2  # seach sucessfull action in this flow should create a log

    app.dependency_overrides = {}


def test_add_client_credit_by_admin_inexistent_vip_client(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    # we do not persist vip client for this test

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"quantity": 10, "reason": "adding credits to test"}

    response = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "vip_client_not_found"

    client_credits = read_uow.client_credit_entries.count_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert client_credits == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )

    assert logs == []

    app.dependency_overrides = {}


def test_add_invalid_quantity_client_credit_by_admin(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"quantity": 0, "reason": "adding credits to test"}

    response = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_credit_quantity"

    client_credits = read_uow.client_credit_entries.count_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert client_credits == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )

    assert logs == []

    app.dependency_overrides = {}


def test_add_client_credit_by_not_admin(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=False, is_active=True, email="not_admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"quantity": 10, "reason": "adding credits to test"}

    response = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    client_credits = read_uow.client_credit_entries.count_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert client_credits == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )

    assert logs == []

    app.dependency_overrides = {}


def test_add_client_credit_by_inactive_admin(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=False, email="not_admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"quantity": 10, "reason": "adding credits to test"}

    response = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    client_credits = read_uow.client_credit_entries.count_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert client_credits == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )

    assert logs == []

    app.dependency_overrides = {}


def test_add_client_credit_by_not_user(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=False, email="not_admin@admin.com")
    # we do not persist user for this test
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"quantity": 10, "reason": "adding credits to test"}

    response = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    client_credits = read_uow.client_credit_entries.count_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert client_credits == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )

    assert logs == []

    app.dependency_overrides = {}


def test_add_client_credit_wrong_payload_type(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {
        "quantity": "this is a string should be a int",
        "reason": "adding credits to test",
    }

    response = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_add_client_credit_missing_payload_field(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {
        "quantity": 10,
        # we are missing reason on payload
    }

    response = client.post(
        f"/client-credit-entries/{vip_client.id}/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_add_client_credit_invalid_vip_client_id(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {
        "quantity": 10,
        "reason": "adding credits to test",
    }

    response = client.post(
        "/client-credit-entries/not_a_uuid/add_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}
