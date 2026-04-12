from fastapi.testclient import TestClient

from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.main import app


client = TestClient(app)


def test_change_vip_client_phone_success(
    make_vip_client, make_user, make_token, write_uow, read_uow
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client(phone="71999999999", email="vip@client.com")
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {"new_phone": "71988888888"}

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/vip-clients/{vip_client.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = read_uow.vip_clients.find_by_id(vip_client.id)
    admin_saved = read_uow.users.find_by_id(admin.id)

    assert response.status_code == 204
    assert vip_client_saved.phone == "71988888888"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_phone_double_call_success(
    make_vip_client, make_user, make_token, write_uow, read_uow
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client(phone="71999999999", email="vip@client.com")
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {"new_phone": "71988888888"}

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    first_call = client.patch(
        f"/vip-clients/{vip_client.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    second_call = client.patch(
        f"/vip-clients/{vip_client.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = read_uow.vip_clients.find_by_id(vip_client.id)
    admin_saved = read_uow.users.find_by_id(admin.id)

    assert first_call.status_code == 204
    assert second_call.status_code == 204
    assert vip_client_saved.phone == "71988888888"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_phone_not_admin(
    make_vip_client, make_user, make_token, write_uow, read_uow
):
    admin = make_user(is_admin=False, is_active=True, email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client(phone="71999999999", email="vip@client.com")
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {"new_phone": "71988888888"}

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/vip-clients/{vip_client.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = read_uow.vip_clients.find_by_id(vip_client.id)
    admin_saved = read_uow.users.find_by_id(admin.id)

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert vip_client_saved.phone == "71999999999"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_phone_not_active(
    make_vip_client, make_user, make_token, write_uow, read_uow
):
    admin = make_user(is_admin=True, is_active=False, email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client(phone="71999999999", email="vip@client.com")
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {"new_phone": "71988888888"}

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/vip-clients/{vip_client.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = read_uow.vip_clients.find_by_id(vip_client.id)
    admin_saved = read_uow.users.find_by_id(admin.id)

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"
    assert vip_client_saved.phone == "71999999999"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_phone_not_user(
    make_vip_client, make_user, make_token, write_uow, read_uow
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    # admin not persisted

    vip_client = make_vip_client(phone="71999999999", email="vip@client.com")
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {"new_phone": "71988888888"}

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/vip-clients/{vip_client.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = read_uow.vip_clients.find_by_id(vip_client.id)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert vip_client_saved.phone == "71999999999"

    app.dependency_overrides = {}


def test_change_vip_client_phone_already_taken(
    make_vip_client, make_user, make_token, write_uow, read_uow
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client1 = make_vip_client(phone="71999999999", email="vip@client.com")
    write_uow.vip_clients.create(vip_client1)

    vip_client2 = make_vip_client(phone="71988888888", email="vip@client.com")
    write_uow.vip_clients.create(vip_client2)

    token = make_token(admin)

    payload = {"new_phone": "71988888888"}

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/vip-clients/{vip_client1.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client1_saved = read_uow.vip_clients.find_by_id(vip_client1.id)
    vip_client2_saved = read_uow.vip_clients.find_by_id(vip_client2.id)
    admin_saved = read_uow.users.find_by_id(admin.id)

    assert response.status_code == 409
    assert response.json()["detail"] == "phone_chosen_is_already_taken"
    assert vip_client1_saved.phone == "71999999999"
    assert vip_client2_saved.phone == "71988888888"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_phone_client_not_found(
    make_vip_client, make_user, make_token, write_uow, read_uow
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client(phone="71999999999", email="vip@client.com")
    # vip client not persisted

    token = make_token(admin)

    payload = {"new_phone": "71988888888"}

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/vip-clients/{vip_client.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "vip_client_not_found"

    app.dependency_overrides = {}


def test_change_vip_client_phone_invalid_phone(
    make_vip_client, make_user, make_token, write_uow, read_uow
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client(phone="71999999999", email="vip@client.com")
    write_uow.vip_clients.create(vip_client)

    token = make_token(admin)

    payload = {"new_phone": "this_is_not_a_phone"}

    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/vip-clients/{vip_client.id}/change-phone",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}
