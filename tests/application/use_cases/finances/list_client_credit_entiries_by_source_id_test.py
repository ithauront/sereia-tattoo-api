from uuid import uuid4

from app.application.studio.use_cases.DTO.commun import Direction
from app.application.studio.use_cases.DTO.list_client_credit_entries import (
    ListCreditEntriesBySourceIdInput,
    ListCreditEntriesOutput,
)
from app.application.studio.use_cases.finances_use_cases.list_credits_entries_by_source_id import (
    ListClientCreditEntriesBySourceIdUseCase,
)
from app.core.types.client_credit_source_type import ClientCreditSourceType


def test_list_credit_entries_by_source_id_admin_default_success(
    make_user, make_client_credit_entry, read_uow, write_uow
):
    admin = make_user()
    write_uow.users.create(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListClientCreditEntriesBySourceIdUseCase(read_uow)
    input_data = ListCreditEntriesBySourceIdInput(source_id=admin.id)

    result = use_case.execute(input_data)

    assert isinstance(result, ListCreditEntriesOutput)

    assert result.total == 10
    assert result.page == 1
    assert result.limit == 20

    assert result.entries[0].quantity == 1
    assert result.entries[0].reason == "this is the entry tested"


def test_list_credit_entries_by_source_id_appointment_default_success(
    make_completed_appointment, make_client_credit_entry, read_uow, write_uow
):
    appointment = make_completed_appointment()
    write_uow.appointments.create(appointment)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=appointment.id, quantity=i, reason="Créditos referentes a indicação."
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=uuid4(), quantity=i, reason="should not appear in this test"
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListClientCreditEntriesBySourceIdUseCase(read_uow)
    input_data = ListCreditEntriesBySourceIdInput(source_id=appointment.id)

    result = use_case.execute(input_data)

    assert isinstance(result, ListCreditEntriesOutput)

    assert result.total == 10
    assert result.page == 1
    assert result.limit == 20

    assert result.entries[0].quantity == 1
    assert result.entries[0].reason == "Créditos referentes a indicação."


def test_list_credit_entries_by_client_id_custom_success(
    make_user, make_client_credit_entry, read_uow, write_uow
):
    admin = make_user()
    write_uow.users.create(admin)

    for i in range(1, 31):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListClientCreditEntriesBySourceIdUseCase(read_uow)
    input_data = ListCreditEntriesBySourceIdInput(source_id=admin.id, page=2, limit=5)

    result = use_case.execute(input_data)

    assert isinstance(result, ListCreditEntriesOutput)

    assert result.total == 30
    assert result.page == 2
    assert result.limit == 5

    assert result.entries[0].quantity == 6


def test_list_result_limit_should_not_exceed_100(
    make_user, make_client_credit_entry, read_uow, write_uow
):
    admin = make_user()
    write_uow.users.create(admin)

    for i in range(1, 151):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListClientCreditEntriesBySourceIdUseCase(read_uow)
    input_data = ListCreditEntriesBySourceIdInput(
        source_id=admin.id,
        limit=999,
    )

    result = use_case.execute(input_data)

    assert result.limit == 100
    assert len(result.entries) == 100
    assert result.total == 150


def test_returns_empty_list_when_no_entries(make_user, read_uow, write_uow):
    admin = make_user()
    write_uow.users.create(admin)

    use_case = ListClientCreditEntriesBySourceIdUseCase(read_uow)

    input_data = ListCreditEntriesBySourceIdInput(source_id=admin.id)

    result = use_case.execute(input_data)

    assert result.total == 0
    assert result.entries == []


def test_page_out_of_range_returns_empty(make_user, make_client_credit_entry, read_uow, write_uow):
    admin = make_user()
    write_uow.users.create(admin)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListClientCreditEntriesBySourceIdUseCase(read_uow)

    input_data = ListCreditEntriesBySourceIdInput(
        source_id=admin.id,
        page=5,
        limit=10,
    )

    result = use_case.execute(input_data)

    assert result.entries == []


def test_direction_desc(make_user, make_client_credit_entry, read_uow, write_uow):
    admin = make_user()
    write_uow.users.create(admin)

    for i in range(1, 4):
        client_credit_entry = make_client_credit_entry(
            source_id=admin.id,
            source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
            quantity=i,
            reason="this is the entry tested",
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListClientCreditEntriesBySourceIdUseCase(read_uow)

    input_data = ListCreditEntriesBySourceIdInput(
        source_id=admin.id,
        direction=Direction.desc,
    )

    result = use_case.execute(input_data)

    assert result.entries[0].quantity == 3
