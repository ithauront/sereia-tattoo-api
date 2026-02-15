from fastapi.testclient import TestClient
from app.api.dependencies.users import get_users_repository
from app.main import app

client = TestClient(app)


def test_change_email_success(repo, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "123456", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.email == "new@email.com"

    app.dependency_overrides = {}


def test_change_email_same_email_idempotent(repo, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "123456", "new_email": "jhon@doe.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.email == "jhon@doe.com"


def test_change_email_normalization(repo, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "123456", "new_email": " New@Email.COM "}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert user.email == "new@email.com"


def test_change_email_wrong_password(repo, make_user, make_token):
    user = make_user(email="jhon@doe.com")
    repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "wrong_password", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "invalid_credentials"
    assert user.email == "jhon@doe.com"

    app.dependency_overrides = {}


def test_change_email_already_taken(repo, make_user, make_token):
    user1 = make_user(email="jhon@doe.com")
    repo.create(user1)
    token = make_token(user1)
    user2 = make_user(email="already@taken.com")
    repo.create(user2)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "123456", "new_email": "already@taken.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "email_chosen_is_already_taken"
    assert user1.email == "jhon@doe.com"

    app.dependency_overrides = {}


def test_inactive_user_change_email(repo, make_user, make_token):
    user = make_user(is_active=False, email="jhon@doe.com")
    repo.create(user)
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo
    payload = {"password": "123456", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_not_user_change_email(repo, make_user, make_token):
    user = make_user()
    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "123456", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_token_type(repo, make_user, make_token):
    user = make_user()
    repo.create(user)
    token = make_token(user, token_type="refresh")

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "123456", "new_email": "new@email.com"}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_payload_types(repo, make_user, make_token):
    user = make_user()
    repo.create(user)

    token = make_token(user)

    app.dependency_overrides[get_users_repository] = lambda: repo

    payload = {"password": "123456", "new_email": 123456}

    response = client.patch(
        "/me/change-email",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["loc"][-1] == "new_email"
