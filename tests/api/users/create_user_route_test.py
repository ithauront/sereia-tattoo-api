from fastapi.testclient import TestClient
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.security import jwt_service
from app.main import app
from tests.fakes.fake_email_service import FakeEmailService
from app.api.dependencies.notifications import get_email_service


client = TestClient(app)


def test_create_user_success(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is not None

    assert response.status_code == 201
    assert (
        response.json()["message"]
        == "User created if you dont recive an email please try resend email option"
    )

    app.dependency_overrides = {}


def test_user_already_exists(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(admin)
    write_uow.users.create(user)

    token = make_token(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert fake_email_service.sent is False
    assert response.status_code == 409
    assert response.json()["detail"] == "user_already_exists"

    app.dependency_overrides = {}


def test_not_admin_create_user(write_uow, read_uow, make_user, make_token):
    not_admin = make_user(is_admin=False, email="admin@admin.com")
    write_uow.users.create(not_admin)

    token = make_token(not_admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"

    app.dependency_overrides = {}


def test_inactive_admin_create_user(write_uow, read_uow, make_user, make_token):
    inactive_admin = make_user(is_admin=True, email="admin@admin.com", is_active=False)
    write_uow.users.create(inactive_admin)

    token = make_token(inactive_admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_non_existent_user_create_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")

    token = make_token(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_wrong_token_type_create_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin, token_type="refresh")

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_missing_authorization_header_create_user(write_uow, read_uow, make_user):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["header", "authorization"]

    app.dependency_overrides = {}


def test_missing_bearer_prefix_create_user(write_uow, read_uow, make_user, make_token):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin, token_type="refresh")

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": f" {token}"},
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_jwt_format_create_user(write_uow, read_uow, make_user):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users",
        json=payload,
        headers={"Authorization": "Bearer abc.def.ghi"},
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_invalid_token_sub_create_user(write_uow, read_uow, make_user):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = jwt_service.create(subject="not-a-uuid", minutes=60, token_type="access")

    payload = {"email": "jhon@doe.com"}

    fake_email_service = FakeEmailService()

    app.dependency_overrides[get_email_service] = lambda: fake_email_service
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.post(
        "/users", json=payload, headers={"Authorization": f" {token}"}
    )

    user_in_users_repo = read_uow.users.find_by_email("jhon@doe.com")
    assert user_in_users_repo is None

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}
