from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (  # noqa: E501
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


def test_find_by_email(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    found = sqlalchemy_vip_clients_repo.find_by_email(vip_client.email)

    assert found is not None
    assert found.first_name == "Jhon"
    assert found.id == vip_client.id


def test_find_by_phone(
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository, make_vip_client
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)

    found = sqlalchemy_vip_clients_repo.find_by_phone(vip_client.phone)

    assert found is not None
    assert found.first_name == "Jhon"
    assert found.id == vip_client.id


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
