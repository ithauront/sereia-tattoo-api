from uuid import uuid4

import pytest

from app.domain.studio.marketing.enums.client_credit_source_type import (
    ClientCreditSourceType,
)
from app.infrastructure.sqlalchemy.repositories.client_credit_entries_repository import (
    SQLAlchemyClientCreditEntriesRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)

from sqlalchemy.exc import IntegrityError


def test_create_and_find_by_id(
    sqlalchemy_client_credits_entries_repo: SQLAlchemyClientCreditEntriesRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    make_vip_client,
    make_client_credit_entry,
):
    vip_client = make_vip_client()

    sqlalchemy_vip_clients_repo.create(vip_client)

    entry = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry)

    found = sqlalchemy_client_credits_entries_repo.find_by_id(entry.id)

    assert found is not None
    assert found.id == entry.id
    assert found.quantity == 10
    assert found.source_type == "indication"


def test_cannot_create_without_vip_client(
    sqlalchemy_client_credits_entries_repo: SQLAlchemyClientCreditEntriesRepository,
    make_client_credit_entry,
):

    entry = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
    )
    with pytest.raises(IntegrityError):
        sqlalchemy_client_credits_entries_repo.create(entry)


def test_get_correct_balance_from_entries(
    sqlalchemy_client_credits_entries_repo: SQLAlchemyClientCreditEntriesRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    make_user,
    make_vip_client,
    make_client_credit_entry,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)
    admin = make_user(is_admin=True)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry1)

    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        source_id=admin.id,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry2)

    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.REVERSED_BY_ADMIN,
        source_id=admin.id,
        vip_client_id=vip_client.id,
        related_entry_id=entry2.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry3)

    entry4 = make_client_credit_entry(
        quantity=5,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry4)

    entry5 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        source_id=uuid4(),  # appointment id
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry5)
    # sum of all must be 5

    balance = sqlalchemy_client_credits_entries_repo.get_balance(
        vip_client_id=vip_client.id
    )

    assert balance == 5


def test_find_many_by_vip_cient_id(
    sqlalchemy_client_credits_entries_repo: SQLAlchemyClientCreditEntriesRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    make_user,
    make_vip_client,
    make_client_credit_entry,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)
    admin = make_user(is_admin=True)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry1)

    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        source_id=admin.id,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry2)

    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.REVERSED_BY_ADMIN,
        source_id=admin.id,
        vip_client_id=vip_client.id,
        related_entry_id=entry2.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry3)

    entry4 = make_client_credit_entry(
        quantity=5,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry4)

    entry5 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        source_id=uuid4(),  # appointment id
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry5)

    result = sqlalchemy_client_credits_entries_repo.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    created_ats = [entry.created_at for entry in result]

    assert created_ats == sorted(created_ats, reverse=True)
    assert result[0].created_at >= result[-1].created_at

    assert len(result) == 5
    assert result[0].vip_client_id == vip_client.id


def test_find_many_by_source_id(
    sqlalchemy_client_credits_entries_repo: SQLAlchemyClientCreditEntriesRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    make_user,
    make_vip_client,
    make_client_credit_entry,
):
    vip_client = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client)
    admin = make_user(is_admin=True)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry1)

    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        source_id=admin.id,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry2)

    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.REVERSED_BY_ADMIN,
        source_id=admin.id,
        vip_client_id=vip_client.id,
        related_entry_id=entry2.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry3)

    entry4 = make_client_credit_entry(
        quantity=5,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry4)

    entry5 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        source_id=uuid4(),  # appointment id
        vip_client_id=vip_client.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry5)

    result = sqlalchemy_client_credits_entries_repo.find_many_by_source_id(
        source_id=admin.id
    )

    created_ats = [entry.created_at for entry in result]

    assert created_ats == sorted(created_ats, reverse=True)
    assert result[0].created_at >= result[-1].created_at

    assert len(result) == 2


def test_find_many_by_source_type_and_vip_client_id(
    sqlalchemy_client_credits_entries_repo: SQLAlchemyClientCreditEntriesRepository,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    make_user,
    make_vip_client,
    make_client_credit_entry,
):
    vip_client1 = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip_client1)

    vip_client2 = make_vip_client(
        phone="71988888888", email="jane@doe.com", client_code="JHON-RED"
    )
    sqlalchemy_vip_clients_repo.create(vip_client2)
    admin = make_user(is_admin=True)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client1.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry1)

    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        source_id=admin.id,
        vip_client_id=vip_client2.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry2)

    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.REVERSED_BY_ADMIN,
        source_id=admin.id,
        vip_client_id=vip_client2.id,
        related_entry_id=entry2.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry3)

    entry4 = make_client_credit_entry(
        quantity=5,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client1.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry4)

    entry5 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        source_id=uuid4(),  # appointment id
        vip_client_id=vip_client2.id,
    )
    sqlalchemy_client_credits_entries_repo.create(entry5)

    result = sqlalchemy_client_credits_entries_repo.find_many_by_source_type_and_vip_client_id(
        vip_client_id=vip_client1.id, source_type=ClientCreditSourceType.INDICATION
    )

    created_ats = [entry.created_at for entry in result]

    assert created_ats == sorted(created_ats, reverse=True)
    assert result[0].created_at >= result[-1].created_at

    assert len(result) == 2
