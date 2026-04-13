from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.application.studio.use_cases.DTO.commun import Direction
from app.domain.studio.finances.enums.client_credit_source_type import (
    ClientCreditSourceType,
)
from tests.fakes.fake_client_credit_entries_repository import (
    FakeClientCreditEntriesRepository,
)
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository


@pytest.fixture
def entry_repo():
    return FakeClientCreditEntriesRepository()


@pytest.fixture
def vip_client_repo():
    return FakeVipClientsRepository()


def test_create_and_find_by_id(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)

    entry = make_client_credit_entry(vip_client_id=vip_client.id)
    entry_repo.create(entry)

    found = entry_repo.find_by_id(entry.id)

    assert found is not None
    assert found.quantity == entry.quantity


def test_find_by_id_returns_none_when_not_found(entry_repo):
    result = entry_repo.find_by_id(uuid4())

    assert result is None


def test_get_balance(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        vip_client_id=vip_client.id,
    )
    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        vip_client_id=vip_client.id,
    )
    # balance must be 10 + 10 - 10 = 10
    entry_repo.create(entry1)
    entry_repo.create(entry2)
    entry_repo.create(entry3)

    balance = entry_repo.get_balance(vip_client_id=vip_client.id)

    assert balance == 10


def test_find_many_by_vip_client_id(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client1 = make_vip_client()
    vip_client_repo.create(vip_client1)
    vip_client2 = make_vip_client()
    vip_client_repo.create(vip_client2)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client1.id,
    )
    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        vip_client_id=vip_client1.id,
    )
    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        vip_client_id=vip_client2.id,
    )

    entry_repo.create(entry1)
    entry_repo.create(entry2)
    entry_repo.create(entry3)

    entries = entry_repo.find_many_by_vip_client_id(vip_client_id=vip_client1.id)

    assert len(entries) == 2


def test_count_by_vip_client_id(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client1 = make_vip_client()
    vip_client_repo.create(vip_client1)

    vip_client2 = make_vip_client()
    vip_client_repo.create(vip_client2)

    entry_repo.create(make_client_credit_entry(vip_client_id=vip_client1.id))
    entry_repo.create(make_client_credit_entry(vip_client_id=vip_client1.id))
    entry_repo.create(make_client_credit_entry(vip_client_id=vip_client2.id))

    count = entry_repo.count_by_vip_client_id(vip_client_id=vip_client1.id)

    assert count == 2


def test_find_many_by_source_id(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client1 = make_vip_client()
    vip_client_repo.create(vip_client1)
    vip_client2 = make_vip_client()
    vip_client_repo.create(vip_client2)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        source_id=vip_client1.id,
    )
    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        source_id=vip_client1.id,
    )
    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        source_id=vip_client2.id,
    )

    entry_repo.create(entry1)
    entry_repo.create(entry2)
    entry_repo.create(entry3)

    entries = entry_repo.find_many_by_source_id(source_id=vip_client1.id)

    assert len(entries) == 2


def test_count_by_source_id(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client1 = make_vip_client()
    vip_client_repo.create(vip_client1)

    vip_client2 = make_vip_client()
    vip_client_repo.create(vip_client2)

    source_id = uuid4()

    entry_repo.create(
        make_client_credit_entry(vip_client_id=vip_client1.id, source_id=source_id)
    )
    entry_repo.create(
        make_client_credit_entry(vip_client_id=vip_client1.id, source_id=source_id)
    )
    entry_repo.create(
        make_client_credit_entry(vip_client_id=vip_client2.id, source_id=source_id)
    )

    count = entry_repo.count_by_source_id(source_id=source_id)

    assert count == 3


def test_find_many_by_source_type_and_vip_client_id(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client1 = make_vip_client()
    vip_client_repo.create(vip_client1)
    vip_client2 = make_vip_client()
    vip_client_repo.create(vip_client2)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client1.id,
    )
    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        vip_client_id=vip_client1.id,
    )
    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        vip_client_id=vip_client2.id,
    )
    entry4 = make_client_credit_entry(
        quantity=30,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client1.id,
    )
    entry_repo.create(entry1)
    entry_repo.create(entry2)
    entry_repo.create(entry3)
    entry_repo.create(entry4)

    entries = entry_repo.find_many_by_source_type_and_vip_client_id(
        source_type=ClientCreditSourceType.INDICATION, vip_client_id=vip_client1.id
    )

    assert len(entries) == 2


def test_count_by_source_type_and_vip_client_id(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client1 = make_vip_client()
    vip_client_repo.create(vip_client1)

    vip_client2 = make_vip_client()
    vip_client_repo.create(vip_client2)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client1.id,
    )
    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        vip_client_id=vip_client1.id,
    )
    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client2.id,
    )
    entry4 = make_client_credit_entry(
        quantity=30,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client1.id,
    )
    entry_repo.create(entry1)
    entry_repo.create(entry2)
    entry_repo.create(entry3)
    entry_repo.create(entry4)

    count = entry_repo.count_by_source_type_and_vip_client_id(
        source_type=ClientCreditSourceType.INDICATION, vip_client_id=vip_client1.id
    )

    assert count == 2


def test_entries_are_ordered_by_created_at_desc(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)

    now = datetime.utcnow()

    entry_old = make_client_credit_entry(
        vip_client_id=vip_client.id,
        created_at=now - timedelta(days=2),
    )

    entry_middle = make_client_credit_entry(
        vip_client_id=vip_client.id,
        created_at=now - timedelta(days=1),
    )

    entry_new = make_client_credit_entry(
        vip_client_id=vip_client.id,
        created_at=now,
    )

    entry_repo.create(entry_old)
    entry_repo.create(entry_middle)
    entry_repo.create(entry_new)

    entries = entry_repo.find_many_by_vip_client_id(vip_client_id=vip_client.id)

    assert entries[0].id == entry_new.id
    assert entries[1].id == entry_middle.id
    assert entries[2].id == entry_old.id


def test_entries_are_ordered_by_created_at_asc(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)

    now = datetime.utcnow()

    entry_old = make_client_credit_entry(
        vip_client_id=vip_client.id,
        created_at=now - timedelta(days=2),
    )

    entry_middle = make_client_credit_entry(
        vip_client_id=vip_client.id,
        created_at=now - timedelta(days=1),
    )

    entry_new = make_client_credit_entry(
        vip_client_id=vip_client.id,
        created_at=now,
    )

    entry_repo.create(entry_old)
    entry_repo.create(entry_middle)
    entry_repo.create(entry_new)

    entries = entry_repo.find_many_by_vip_client_id(
        vip_client_id=vip_client.id, direction=Direction.asc
    )

    assert entries[2].id == entry_new.id
    assert entries[1].id == entry_middle.id
    assert entries[0].id == entry_old.id


def test_pagination_works(
    make_vip_client, make_client_credit_entry, entry_repo, vip_client_repo
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)

    entry1 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    entry2 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        vip_client_id=vip_client.id,
    )
    entry3 = make_client_credit_entry(
        quantity=10,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )
    entry4 = make_client_credit_entry(
        quantity=30,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )

    entry5 = make_client_credit_entry(
        quantity=50,
        source_type=ClientCreditSourceType.INDICATION,
        vip_client_id=vip_client.id,
    )

    entry_repo.create(entry1)
    entry_repo.create(entry2)
    entry_repo.create(entry3)
    entry_repo.create(entry4)
    entry_repo.create(entry5)

    entries = entry_repo.find_many_by_vip_client_id(
        vip_client_id=vip_client.id,
        limit=2,
        offset=1,
    )

    assert len(entries) == 2


def test_order_tie_break_by_id(
    make_client_credit_entry, entry_repo, make_vip_client, vip_client_repo
):
    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)

    now = datetime.utcnow()

    entry1 = make_client_credit_entry(
        vip_client_id=vip_client.id,
        created_at=now,
    )

    entry2 = make_client_credit_entry(
        vip_client_id=vip_client.id,
        created_at=now,
    )

    entry1.id = uuid4()
    entry2.id = uuid4()

    entry_repo.create(entry1)
    entry_repo.create(entry2)

    entries_desc = entry_repo.find_many_by_vip_client_id(
        vip_client_id=vip_client.id,
        direction=Direction.desc,
    )

    expected_desc = sorted(
        [entry1, entry2],
        key=lambda e: (e.created_at, e.id),
        reverse=True,
    )

    assert entries_desc[0].id == expected_desc[0].id
    assert entries_desc[1].id == expected_desc[1].id

    entries_asc = entry_repo.find_many_by_vip_client_id(
        vip_client_id=vip_client.id,
        direction=Direction.asc,
    )

    expected_asc = sorted(
        [entry1, entry2],
        key=lambda e: (e.created_at, e.id),
        reverse=False,
    )

    assert entries_asc[0].id == expected_asc[0].id
    assert entries_asc[1].id == expected_asc[1].id
