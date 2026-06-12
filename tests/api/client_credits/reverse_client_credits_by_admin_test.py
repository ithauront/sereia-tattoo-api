from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.main import app

client = TestClient(app)


def test_reverse_client_credit_by_admin_default(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.INDICATION
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["vip_client_id"] == str(vip_client.id)
    assert data["original_credit_id"] == str(original_credit.id)
    assert data["total_credits_before"] == 10
    assert data["total_credits_after"] == 0

    reversed_credit_id = data["reversed_credit_id"]

    credit_entry = read_uow.client_credit_entries.find_by_id(UUID(reversed_credit_id))

    assert credit_entry.related_entry_id == original_credit.id
    assert credit_entry.quantity == -10

    app.dependency_overrides = {}


def test_reverse_client_credit_creates_log(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.INDICATION
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")
    assert len(logs) == 1
    assert logs[0].action == "admin reverse credits"

    app.dependency_overrides = {}


def test_reverse_client_credit_by_admin_two_calls(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.INDICATION
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    first_call = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    second_call = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first_call.status_code == 201
    assert second_call.status_code == 400
    assert second_call.json()["detail"] == "credit_was_already_reversed_before"

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(client_credits) == 2

    assert any(c.source_type == ClientCreditSourceType.REVERSED_BY_ADMIN for c in client_credits)
    assert any(c.source_type == ClientCreditSourceType.INDICATION for c in client_credits)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert len(logs) == 1

    app.dependency_overrides = {}


def test_reverse_client_credit_vip_client_not_found(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.INDICATION
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(uuid4())}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "vip_client_not_found"

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(client_credits) == 1

    assert client_credits[0].source_type == ClientCreditSourceType.INDICATION

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert logs == []

    app.dependency_overrides = {}


def test_reverse_negative_credit_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "cannot_reverse_negative_credit"
    assert response.json()["detail"]["message"] == "This credit is negative and cannot be reversed."
    assert (
        response.json()["detail"]["hint"]
        == "Create an opposite credit entry and provide a reason and related_entry_id."
    )

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(client_credits) == 1

    assert client_credits[0].source_type == ClientCreditSourceType.USED_IN_APPOINTMENT

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert logs == []

    app.dependency_overrides = {}


def test_reverse_already_reversed_credit_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.INDICATION
    )
    write_uow.client_credit_entries.create(original_credit)

    reverse_credit = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.REVERSED_BY_ADMIN,
        related_entry_id=original_credit.id,
    )
    write_uow.client_credit_entries.create(reverse_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "credit_was_already_reversed_before"

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(client_credits) == 2

    assert any(c.source_type == ClientCreditSourceType.REVERSED_BY_ADMIN for c in client_credits)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert logs == []

    app.dependency_overrides = {}


def test_reverse_not_found_credit_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    # we do not persist credit for this test

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "credit_not_found"

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(client_credits) == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert logs == []

    app.dependency_overrides = {}


def test_reverse_credit_by_not_admin_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=False, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(client_credits) == 1

    assert client_credits[0].source_type == ClientCreditSourceType.USED_IN_APPOINTMENT

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert logs == []

    app.dependency_overrides = {}


def test_reverse_credit_by_inactive_admin_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=False, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(client_credits) == 1

    assert client_credits[0].source_type == ClientCreditSourceType.USED_IN_APPOINTMENT

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert logs == []

    app.dependency_overrides = {}


def test_reverse_credit_by_not_user_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    # we do not persist user for this test
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(client_credits) == 1

    assert client_credits[0].source_type == ClientCreditSourceType.USED_IN_APPOINTMENT

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert logs == []

    app.dependency_overrides = {}


def test_reverse_credit_wrong_payload_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {
        "reason": "reversing credits to test",
        "vip_client_id": "not-a-uuid",
    }

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_reverse_credit_missing_payload_field_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test"}  # should have vip id

    response = client.post(
        f"/client-credit-entries/{original_credit.id}/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_reverse_credit_invalid_original_credit_id_error(
    write_uow, read_uow, make_user, make_token, make_vip_client, make_client_credit_entry
):
    user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(user)
    token = make_token(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credit = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    write_uow.client_credit_entries.create(original_credit)

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    payload = {"reason": "reversing credits to test", "vip_client_id": str(vip_client.id)}

    response = client.post(
        "/client-credit-entries/not_a_uuid/reverse_credits",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}
