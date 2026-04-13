from app.application.studio.use_cases.DTO.list_client_credit_entries import (
    ListCreditEntriesByClientIdInput,
    ListCreditEntriesOutput,
)
from app.application.studio.use_cases.finances_use_cases.list_credit_entries_by_client_id import (
    ListCreditEntriesByClientIdUseCase,
)


def test_list_credit_entries_by_client_id_default_success(
    make_vip_client, make_client_credit_entry, read_uow, write_uow
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 11):
        client_credit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListCreditEntriesByClientIdUseCase(read_uow)
    input_data = ListCreditEntriesByClientIdInput(vip_client_id=vip_client.id)

    result = use_case.execute(input_data)

    assert isinstance(result, ListCreditEntriesOutput)

    assert result.total == 10
    assert result.page == 1
    assert result.limit == 20

    assert result.entries[0].quantity == 1


def test_list_credit_entries_by_client_id_custom_success(
    make_vip_client, make_client_credit_entry, read_uow, write_uow
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 31):
        client_credit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListCreditEntriesByClientIdUseCase(read_uow)
    input_data = ListCreditEntriesByClientIdInput(
        vip_client_id=vip_client.id, page=2, limit=5
    )

    result = use_case.execute(input_data)

    assert isinstance(result, ListCreditEntriesOutput)

    assert result.total == 30
    assert result.page == 2
    assert result.limit == 5

    assert result.entries[0].quantity == 6


def test_list_result_limit_should_not_exceed_100(
    make_vip_client, make_client_credit_entry, read_uow, write_uow
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 151):
        client_credit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id, quantity=i
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = ListCreditEntriesByClientIdUseCase(read_uow)
    input_data = ListCreditEntriesByClientIdInput(
        vip_client_id=vip_client.id,
        limit=999,
    )

    result = use_case.execute(input_data)

    assert result.limit == 100
    assert len(result.entries) == 100
    assert result.total == 150


def test_returns_empty_list_when_no_entries(make_vip_client, read_uow, write_uow):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    use_case = ListCreditEntriesByClientIdUseCase(read_uow)

    input_data = ListCreditEntriesByClientIdInput(vip_client_id=vip_client.id)

    result = use_case.execute(input_data)

    assert result.total == 0
    assert result.entries == []


def test_page_out_of_range_returns_empty(
    make_vip_client, make_client_credit_entry, read_uow, write_uow
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 11):
        write_uow.client_credit_entries.create(
            make_client_credit_entry(vip_client_id=vip_client.id)
        )

    use_case = ListCreditEntriesByClientIdUseCase(read_uow)

    input_data = ListCreditEntriesByClientIdInput(
        vip_client_id=vip_client.id,
        page=5,
        limit=10,
    )

    result = use_case.execute(input_data)

    assert result.entries == []


def test_direction_desc(make_vip_client, make_client_credit_entry, read_uow, write_uow):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    for i in range(1, 4):
        write_uow.client_credit_entries.create(
            make_client_credit_entry(
                vip_client_id=vip_client.id,
                quantity=i,
            )
        )

    use_case = ListCreditEntriesByClientIdUseCase(read_uow)

    input_data = ListCreditEntriesByClientIdInput(
        vip_client_id=vip_client.id,
        direction="desc",
    )

    result = use_case.execute(input_data)

    assert result.entries[0].quantity == 3
