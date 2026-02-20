from app.api.dependencies.users import get_users_repository
from app.api.dependencies.vip_clients import get_vip_clients_repository
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_generate_client_codes_success(
    vip_clients_repo, make_user, make_token, users_repo
):
    admin = make_user(is_admin=True)
    users_repo.create(admin)

    token = make_token(admin)

    payload = {"name": "jhon"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.post(
        "/users/vip-client/generate-client-codes",
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
    vip_clients_repo, make_user, make_token, users_repo, mocker
):
    admin = make_user(is_admin=True)
    users_repo.create(admin)

    token = make_token(admin)

    payload = {"name": "jhon"}

    mocker.patch.object(vip_clients_repo, "find_by_client_code", return_value=True)

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.post(
        "/users/vip-client/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "please_try_creating_client_code_with_last_name"

    app.dependency_overrides = {}


def test_generate_client_code_wrong_payload(
    vip_clients_repo, make_user, make_token, users_repo
):
    admin = make_user(is_admin=True)
    users_repo.create(admin)

    token = make_token(admin)

    payload = {"wrong": "payload"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.post(
        "/users/vip-client/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_not_admin_try_to_generate_client_codes(
    vip_clients_repo, make_user, make_token, users_repo
):
    not_admin = make_user(is_admin=False)

    users_repo.create(not_admin)

    token = make_token(not_admin)

    payload = {"name": "jhon"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.post(
        "/users/vip-client/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    app.dependency_overrides = {}


def test_not_active_try_to_generate_client_codes(
    vip_clients_repo, make_user, make_token, users_repo
):
    not_active = make_user(is_admin=True, is_active=False)

    users_repo.create(not_active)

    token = make_token(not_active)

    payload = {"name": "jhon"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.post(
        "/users/vip-client/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_try_to_generate_client_codes(
    vip_clients_repo, make_user, make_token, users_repo
):
    not_user = make_user(is_admin=True, is_active=True)

    # do not create on repo to simulate not_user

    token = make_token(not_user)

    payload = {"name": "jhon"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.post(
        "/users/vip-client/generate-client-codes",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}
