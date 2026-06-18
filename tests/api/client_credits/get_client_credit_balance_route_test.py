from fastapi.testclient import TestClient

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.main import app

client = TestClient(app)


def test_get_client_credit_balance_success(
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

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    for _ in range(10):
        client_credit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id,
            source_type=ClientCreditSourceType.INDICATION,
            quantity=10,
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    client_credit_entry_used = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_id=admin.id,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        quantity=20,
        reason="Teste de credito adicionado por admin",
    )
    write_uow.client_credit_entries.create(client_credit_entry_used)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/balance/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["balance"] == 80

    app.dependency_overrides = {}


def test_get_client_not_found_returns_404(
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

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    # we do not persist client for this test

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/balance/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    data = response.json()

    assert data["detail"] == "vip_client_not_found"

    app.dependency_overrides = {}


def test_get_client_credit_balance_not_user_cannot_access(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)

    not_user = make_user(is_admin=True, is_active=True)
    # we do not persist not_user for this test
    token = make_token(not_user)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    for _ in range(10):
        client_credit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id,
            source_type=ClientCreditSourceType.INDICATION,
            quantity=10,
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    client_credit_entry_used = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_id=admin.id,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        quantity=20,
        reason="Teste de credito adicionado por admin",
    )
    write_uow.client_credit_entries.create(client_credit_entry_used)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/balance/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_get_client_credit_balance_inactive_user_cannot_access(
    write_uow,
    read_uow,
    make_user,
    make_token,
    make_vip_client,
    make_client_credit_entry,
):
    admin = make_user(is_admin=True, is_active=True)
    write_uow.users.create(admin)

    inactive_user = make_user(is_admin=True, is_active=False)
    write_uow.users.create(inactive_user)
    token = make_token(inactive_user)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    for _ in range(10):
        client_credit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id,
            source_type=ClientCreditSourceType.INDICATION,
            quantity=10,
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    client_credit_entry_used = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_id=admin.id,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        quantity=20,
        reason="Teste de credito adicionado por admin",
    )
    write_uow.client_credit_entries.create(client_credit_entry_used)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        f"/client-credit-entries/balance/{vip_client.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}
