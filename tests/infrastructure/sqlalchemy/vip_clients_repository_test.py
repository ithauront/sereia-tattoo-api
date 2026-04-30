import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.studio.users.entities.vip_client import VipClient
from app.domain.studio.value_objects.client_code import ClientCode
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)


def test_create_and_find_by_id(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    found = sqlalchemy_vip_clients_repo.find_by_id(vip_client.id)

    assert found is not None
    assert found.first_name == "Jhon"
    assert found.id == vip_client.id


def test_first_name_not_nullable(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client = make_vip_client(first_name=None)

    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_vip_clients_repo.create(vip_client)

    assert "NOT NULL constraint failed" in str(exc.value)


def test_email_must_be_unique_constraint(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client1 = make_vip_client(email="jhon@doe.com")
    sqlalchemy_vip_clients_repo.create(vip_client1)

    vip_client2 = make_vip_client(email="jhon@doe.com")
    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_vip_clients_repo.create(vip_client2)

    assert "UNIQUE constraint failed" in str(exc.value)


def test_phone_must_be_unique_constraint(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client1 = make_vip_client(phone="71999999999")
    sqlalchemy_vip_clients_repo.create(vip_client1)

    vip_client2 = make_vip_client(phone="71999999999")
    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_vip_clients_repo.create(vip_client2)

    assert "UNIQUE constraint failed" in str(exc.value)


def test_client_code_must_be_unique_constraint(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client1 = make_vip_client(
        client_code="JHON-AZUL"
    )  # factory already transform str in ClientCode
    sqlalchemy_vip_clients_repo.create(vip_client1)

    vip_client2 = make_vip_client(client_code="JHON-AZUL")
    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_vip_clients_repo.create(vip_client2)

    assert "UNIQUE constraint failed" in str(exc.value)


def test_find_by_email(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    found = sqlalchemy_vip_clients_repo.find_by_email(vip_client.email)

    assert found is not None
    assert found.first_name == "Jhon"
    assert found.id == vip_client.id


def test_find_by_client_code(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client = make_vip_client(client_code="JHON-BLUE")
    sqlalchemy_vip_clients_repo.create(vip_client)

    found = sqlalchemy_vip_clients_repo.find_by_client_code("JHON-BLUE")

    assert found is not None
    assert found.first_name == "Jhon"
    assert found.id == vip_client.id
    assert found.client_code.value == "JHON-BLUE"


def test_find_many(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    i: int = 1
    while i <= 4:
        vip_client = make_vip_client(
            email=f"jhon{i}@doe",
            phone=f"719{i}{i}{i}{i}{i}{i}{i}{i}",
            client_code=f"JHON-BLUE-{i:02d}",
        )
        sqlalchemy_vip_clients_repo.create(vip_client)
        i = i + 1

    founds = sqlalchemy_vip_clients_repo.find_many()

    assert len(founds) == 4
    phones = [c.phone for c in founds]
    assert set(phones) == {
        "71911111111",
        "71922222222",
        "71933333333",
        "71944444444",
    }


def test_update_vip_client(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    new_vip_client = VipClient(
        id=vip_client.id,
        first_name="New",
        last_name="Client",
        email="new@client.com",
        phone="71922222222",
        client_code=ClientCode("NEW-CLIENT"),
        created_at=vip_client.created_at,
    )

    before = sqlalchemy_vip_clients_repo.find_by_id(vip_client.id)

    sqlalchemy_vip_clients_repo.update(new_vip_client)

    after = sqlalchemy_vip_clients_repo.find_by_id(vip_client.id)

    assert after is not None
    assert before is not None
    assert after.email == "new@client.com"
    assert after.phone == "71922222222"
    assert after.first_name == "New"
    assert after.last_name == "Client"
    assert after.client_code.value == "NEW-CLIENT"


def test_update_does_not_modify_immutable_fields(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    new_vip_client = VipClient(
        id=vip_client.id,
        first_name="New",
        last_name="Client",
        email="new@client.com",
        phone="71922222222",
        client_code=ClientCode("NEW-CLIENT"),
        created_at=None,
    )

    before = sqlalchemy_vip_clients_repo.find_by_id(vip_client.id)

    sqlalchemy_vip_clients_repo.update(new_vip_client)

    after = sqlalchemy_vip_clients_repo.find_by_id(vip_client.id)

    assert after is not None
    assert before is not None
    assert after.email == "new@client.com"
    assert after.phone == "71922222222"
    assert after.first_name == "New"
    assert after.last_name == "Client"
    assert after.client_code.value == "NEW-CLIENT"

    assert after.created_at == before.created_at


def test_update_respects_unique_constraint(
    sqlalchemy_vip_clients_repo, make_vip_client
):
    vip_client1 = make_vip_client(email="jhon@doe.com")
    vip_client2 = make_vip_client(
        email="jane@doe.com", phone="71922222222", client_code="JANE-RED"
    )
    sqlalchemy_vip_clients_repo.create(vip_client1)
    sqlalchemy_vip_clients_repo.create(vip_client2)

    vip_client2.email = "jhon@doe.com"

    with pytest.raises(IntegrityError):
        sqlalchemy_vip_clients_repo.update(vip_client2)


def test_update_not_found(sqlalchemy_vip_clients_repo, make_vip_client):
    vip_client = make_vip_client()

    result = sqlalchemy_vip_clients_repo.update(vip_client)

    assert result is None


def test_persistence_roundtrip(sqlalchemy_vip_clients_repo, make_vip_client):
    vip_client = make_vip_client(
        first_name="John",
        last_name="Doe",
        email="john@doe.com",
        phone="123",
        client_code="JOHN-AZUL",
    )

    sqlalchemy_vip_clients_repo.create(vip_client)

    found = sqlalchemy_vip_clients_repo.find_by_id(vip_client.id)

    assert found.first_name == "John"
    assert found.last_name == "Doe"
    assert found.client_code.value == "JOHN-AZUL"
