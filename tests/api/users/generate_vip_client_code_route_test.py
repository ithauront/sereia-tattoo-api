from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_generate_client_codes_success(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {"name": "jhon"}

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()
    assert "codes" in data
    assert len(data["codes"]) == 3

    assert all(code.startswith("JHON-") for code in data["codes"])

    app.dependency_overrides = {}


def test_generate_client_code_repo_full(
    write_uow, read_uow, make_user, make_token, mocker
):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {"name": "jhon"}

    mocker.patch.object(read_uow.vip_clients, "find_by_client_code", return_value=True)

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "please_try_creating_client_code_with_last_name"

    app.dependency_overrides = {}


def test_generate_client_code_wrong_payload(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {"wrong": "payload"}

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_not_admin_try_to_generate_client_codes(
    write_uow,
    read_uow,
    make_user,
    make_token,
):
    not_admin = make_user(is_admin=False)

    write_uow.users.create(not_admin)

    token = make_token(not_admin)

    payload = {"name": "jhon"}

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    app.dependency_overrides = {}


def test_not_active_try_to_generate_client_codes(
    write_uow, read_uow, make_user, make_token
):
    not_active = make_user(is_admin=True, is_active=False)

    write_uow.users.create(not_active)

    token = make_token(not_active)

    payload = {"name": "jhon"}

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_try_to_generate_client_codes(read_uow, make_user, make_token):
    not_user = make_user(is_admin=True, is_active=True)

    # do not create on repo to simulate not_user

    token = make_token(not_user)

    payload = {"name": "jhon"}

    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/vip-clients/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}
