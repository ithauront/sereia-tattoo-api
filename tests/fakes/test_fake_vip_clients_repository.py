import pytest
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository


@pytest.fixture
def repo():
    return FakeVipClientsRepository()


def test_create_and_find_by_id(repo, make_vip_client):
    vip_client = make_vip_client()
    repo.create(vip_client)

    found = repo.find_by_id(vip_client.id)

    assert found is not None
    assert found.first_name == vip_client.first_name


def test_find_by_email(repo, make_vip_client):
    vip_client = make_vip_client()
    repo.create(vip_client)

    found = repo.find_by_email(vip_client.email)
    not_found = repo.find_by_email("wrong@email.com")

    assert found is not None
    assert found.first_name == vip_client.first_name
    assert found.email == "jhon@doe.com"
    assert not_found is None


def test_find_by_phone(repo, make_vip_client):
    vip_client = make_vip_client()
    repo.create(vip_client)

    found = repo.find_by_phone(vip_client.phone)
    not_found = repo.find_by_phone("71922222222")

    assert found is not None
    assert found.first_name == vip_client.first_name
    assert found.phone == "71999999999"
    assert not_found is None


def test_find_by_client_code(repo, make_vip_client):
    vip_client = make_vip_client(client_code="JHON-BLUE")
    repo.create(vip_client)

    found = repo.find_by_client_code("JHON-BLUE")
    not_found = repo.find_by_client_code("JHON-GREEN")

    assert found is not None
    assert found.first_name == vip_client.first_name
    assert found.client_code.value == "JHON-BLUE"
    assert not_found is None


def test_update(repo, make_vip_client):
    vip_client = make_vip_client()
    repo.create(vip_client)
    vip_client.phone = "71911111111"
    vip_client.email = "new@email.com"
    repo.update(vip_client)

    found = repo.find_by_email("new@email.com")
    not_found = repo.find_by_email("jhon@doe.com")

    assert found is not None
    assert found.phone == "71911111111"
    assert found.first_name == "Jhon"

    assert not_found is None


def test_find_many(repo, make_vip_client):
    vip_client_1 = make_vip_client(email="jhon@doe.com", phone="71911111111")
    vip_client_2 = make_vip_client(email="jane@doe.com", phone="71922222222")
    vip_client_3 = make_vip_client(email="james@doe.com", phone="71933333333")
    vip_client_4 = make_vip_client(email="janice@doe.com", phone="71944444444")

    repo.create(vip_client_1)
    repo.create(vip_client_2)
    repo.create(vip_client_3)
    repo.create(vip_client_4)

    founds = repo.find_many()

    assert len(founds) == 4
    phones = [c.phone for c in founds]
    assert set(phones) == {
        "71911111111",
        "71922222222",
        "71933333333",
        "71944444444",
    }
