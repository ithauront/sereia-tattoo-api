from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.main import app


client = TestClient(app)


def test_list_vip_clients_default_success(
    write_uow, read_uow, make_user, make_token, make_vip_client
):
    user = make_user(is_admin=False, is_active=True, username="User")

    write_uow.users.create(user)

    vip_client1 = make_vip_client(first_name="Daniela")
    vip_client2 = make_vip_client(first_name="Carla")
    vip_client3 = make_vip_client(first_name="Bernard")
    vip_client4 = make_vip_client(first_name="Adonis")

    write_uow.vip_clients.create(vip_client1)
    write_uow.vip_clients.create(vip_client2)
    write_uow.vip_clients.create(vip_client3)
    write_uow.vip_clients.create(vip_client4)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients",
        headers={"Authorization": f"Bearer {token}"},
    )

    print(response.json())

    name_of_the_first = response.json()["vip_clients"][0]["first_name"]
    assert len(response.json()["vip_clients"]) == 4
    assert response.status_code == 200
    assert name_of_the_first == "Adonis"

    app.dependency_overrides = {}


def test_list_vip_clients_custom_queries_success(
    write_uow, read_uow, make_user, make_token, make_vip_client
):
    user = make_user(is_admin=False, is_active=True, username="User")

    write_uow.users.create(user)

    vip_client1 = make_vip_client(last_name="Dumas")
    vip_client2 = make_vip_client(last_name="Correia")
    vip_client3 = make_vip_client(last_name="Bispo")
    vip_client4 = make_vip_client(last_name="Americo")

    write_uow.vip_clients.create(vip_client1)
    write_uow.vip_clients.create(vip_client2)
    write_uow.vip_clients.create(vip_client3)
    write_uow.vip_clients.create(vip_client4)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients?direction=desc&order_by=last_name",
        headers={"Authorization": f"Bearer {token}"},
    )

    name_of_the_first = response.json()["vip_clients"][0]["last_name"]
    assert len(response.json()["vip_clients"]) == 4
    assert response.status_code == 200
    assert name_of_the_first == "Dumas"

    app.dependency_overrides = {}


def test_list_vip_clients_inactive_user(
    write_uow, read_uow, make_user, make_token, make_vip_client
):
    user = make_user(is_admin=False, is_active=False, username="User")

    write_uow.users.create(user)

    vip_client1 = make_vip_client(first_name="Daniela")
    vip_client2 = make_vip_client(first_name="Carla")
    vip_client3 = make_vip_client(first_name="Bernard")
    vip_client4 = make_vip_client(first_name="Adonis")

    write_uow.vip_clients.create(vip_client1)
    write_uow.vip_clients.create(vip_client2)
    write_uow.vip_clients.create(vip_client3)
    write_uow.vip_clients.create(vip_client4)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_list_vip_clients_not_user(
    write_uow, read_uow, make_user, make_token, make_vip_client
):
    user = make_user(is_admin=False, is_active=True, username="User")

    # Do not persist user

    vip_client1 = make_vip_client(first_name="Daniela")
    vip_client2 = make_vip_client(first_name="Carla")
    vip_client3 = make_vip_client(first_name="Bernard")
    vip_client4 = make_vip_client(first_name="Adonis")

    write_uow.vip_clients.create(vip_client1)
    write_uow.vip_clients.create(vip_client2)
    write_uow.vip_clients.create(vip_client3)
    write_uow.vip_clients.create(vip_client4)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_list_vip_clients_negative_page(read_uow, write_uow, make_user, make_token):
    user = make_user(is_admin=False, is_active=True, username="User")

    write_uow.users.create(user)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients?page=-1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_vip_clients_invalid_limit(write_uow, read_uow, make_user, make_token):
    user = make_user(is_admin=False, is_active=True, username="User")

    write_uow.users.create(user)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients?limit=0",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_users_invalid_order_by(write_uow, read_uow, make_user, make_token):
    user = make_user(is_admin=False, is_active=True, username="User")

    write_uow.users.create(user)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients?order_by=invalid_field",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_list_users_invalid_direction(write_uow, read_uow, make_user, make_token):
    user = make_user(is_admin=False, is_active=True, username="User")

    write_uow.users.create(user)

    token = make_token(user)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.get(
        "/vip-clients?direction=sideways",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}
