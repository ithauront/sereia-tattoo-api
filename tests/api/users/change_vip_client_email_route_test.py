from uuid import uuid4
from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.api.dependencies.vip_clients import get_vip_clients_repository
from app.main import app


client = TestClient(app)


def test_change_vip_client_email_success(
    make_vip_client, make_user, make_token, users_repo, vip_clients_repo
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    users_repo.create(admin)

    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    token = make_token(admin)

    payload = {"new_email": "new@email.com"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.patch(
        f"/users/vip-client/change-email/{vip_client.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = vip_clients_repo.find_by_id(vip_client.id)
    admin_saved = users_repo.find_by_id(admin.id)

    assert response.status_code == 204
    assert vip_client_saved.email == "new@email.com"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_email_same_email_idempotent(
    make_vip_client, make_user, make_token, users_repo, vip_clients_repo
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    users_repo.create(admin)

    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    token = make_token(admin)

    payload = {"new_email": "jhon@doe.com"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.patch(
        f"/users/vip-client/change-email/{vip_client.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = vip_clients_repo.find_by_id(vip_client.id)
    admin_saved = users_repo.find_by_id(admin.id)

    assert response.status_code == 204
    assert vip_client_saved.email == "jhon@doe.com"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_email_not_admin(
    make_vip_client, make_user, make_token, users_repo, vip_clients_repo
):
    not_admin = make_user(is_admin=False, is_active=True, email="admin@admin.com")
    users_repo.create(not_admin)

    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    token = make_token(not_admin)

    payload = {"new_email": "new@email.com"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.patch(
        f"/users/vip-client/change-email/{vip_client.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = vip_clients_repo.find_by_id(vip_client.id)
    admin_saved = users_repo.find_by_id(not_admin.id)

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert vip_client_saved.email == "jhon@doe.com"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_email_not_active(
    make_vip_client, make_user, make_token, users_repo, vip_clients_repo
):
    not_admin = make_user(is_admin=True, is_active=False, email="admin@admin.com")
    users_repo.create(not_admin)

    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    token = make_token(not_admin)

    payload = {"new_email": "new@email.com"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.patch(
        f"/users/vip-client/change-email/{vip_client.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = vip_clients_repo.find_by_id(vip_client.id)
    admin_saved = users_repo.find_by_id(not_admin.id)

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"
    assert vip_client_saved.email == "jhon@doe.com"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_email_not_user(
    make_vip_client, make_user, make_token, users_repo, vip_clients_repo
):
    not_saved_user = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    # do not create user in repo to simulate a non user request

    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    token = make_token(not_saved_user)

    payload = {"new_email": "new@email.com"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.patch(
        f"/users/vip-client/change-email/{vip_client.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = vip_clients_repo.find_by_id(vip_client.id)

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"
    assert vip_client_saved.email == "jhon@doe.com"

    app.dependency_overrides = {}


def test_change_vip_client_email_already_taken(
    make_vip_client, make_user, make_token, users_repo, vip_clients_repo
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    users_repo.create(admin)

    vip_client = make_vip_client(email="jhon@doe.com")
    vip_client_email_taken = make_vip_client(email="new@email.com")
    vip_clients_repo.create(vip_client)
    vip_clients_repo.create(vip_client_email_taken)

    token = make_token(admin)

    payload = {"new_email": "new@email.com"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.patch(
        f"/users/vip-client/change-email/{vip_client.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = vip_clients_repo.find_by_id(vip_client.id)
    admin_saved = users_repo.find_by_id(admin.id)

    assert response.status_code == 409
    assert response.json()["detail"] == "email_chosen_is_already_taken"
    assert vip_client_saved.email == "jhon@doe.com"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_email_not_found(
    make_vip_client, make_user, make_token, users_repo, vip_clients_repo
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    users_repo.create(admin)

    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)
    wrong_id = uuid4()

    token = make_token(admin)

    payload = {"new_email": "new@email.com"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.patch(
        f"/users/vip-client/change-email/{wrong_id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    vip_client_saved = vip_clients_repo.find_by_id(vip_client.id)
    admin_saved = users_repo.find_by_id(admin.id)

    assert response.status_code == 404
    assert response.json()["detail"] == "vip_client_not_found"
    assert vip_client_saved.email == "jhon@doe.com"
    assert admin_saved.email == "admin@admin.com"

    app.dependency_overrides = {}


def test_change_vip_client_email_invalid_email(
    make_user, make_token, make_vip_client, users_repo, vip_clients_repo
):
    # request body type test
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    users_repo.create(admin)

    vip_client = make_vip_client(email="jhon@doe.com")
    vip_clients_repo.create(vip_client)

    token = make_token(admin)

    payload = {"new_email": "not-email"}

    app.dependency_overrides[get_users_repository] = lambda: users_repo
    app.dependency_overrides[get_vip_clients_repository] = lambda: vip_clients_repo

    response = client.patch(
        f"/users/vip-client/change-email/{vip_client.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}
