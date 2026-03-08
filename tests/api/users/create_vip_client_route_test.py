from app.api.dependencies.notifications import get_email_service
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.main import app
from fastapi.testclient import TestClient

from tests.fakes.fake_email_service import FakeEmailService


client = TestClient(app)


def test_create_vip_client_successful(write_uow, read_uow, make_user, make_token):
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is not None
    assert response.status_code == 201

    assert response.json()["message"] == "VIP Client created"

    app.dependency_overrides = {}


def test_vip_client_email_taken(
    write_uow, read_uow, make_user, make_token, make_vip_client
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
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

    app.dependency_overrides = {}


def test_vip_client_phone_taken(
    write_uow, read_uow, make_user, make_token, make_vip_client
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
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

    app.dependency_overrides = {}


def test_vip_client_code_taken(
    write_uow, read_uow, make_user, make_token, make_vip_client
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
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

    app.dependency_overrides = {}


def test_invalid_email_triggers_validation_error(
    write_uow, read_uow, make_user, make_token
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None
    assert response.status_code == 422

    app.dependency_overrides = {}


def test_not_admin_create_vip_client(write_uow, read_uow, make_user, make_token):
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    app.dependency_overrides = {}


def test_inactive_admin_create_vip_client(write_uow, read_uow, make_user, make_token):
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_non_existent_user_create_vip_client(
    write_uow, read_uow, make_user, make_token
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_token_type_create_vip_client(write_uow, read_uow, make_user, make_token):
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

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users/vip-client",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_in_repo = read_uow.vip_clients.find_by_email("jhon@doe.com")
    assert vip_client_in_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}
