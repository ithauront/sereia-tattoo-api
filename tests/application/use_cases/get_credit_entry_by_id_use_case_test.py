import pytest

from app.application.studio.use_cases.DTO.get_client_credit_entries import (
    CreditEntryDetailsOutput,
    GetCreditEntryDetailsByIdInput,
)
from app.application.studio.use_cases.finances_use_cases.get_credit_entry_details_by_id import (
    GetCreditEntryDetailsByIdUseCase,
)
from app.core.exceptions.marketing import CreditEntryNotFoundError
from app.core.exceptions.users import UserNotFoundError, VipClientNotFoundError
from app.domain.studio.finances.enums.client_credit_source_type import (
    ClientCreditSourceType,
)


def test_get_credit_entry_by_id_indication_type_success(
    make_vip_client, make_client_credit_entry, read_uow, write_uow
):
    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.INDICATION,
        quantity=20,
    )
    # Indication type make credit details output without admin_name
    write_uow.client_credit_entries.create(client_credit_entry)

    use_case = GetCreditEntryDetailsByIdUseCase(read_uow)
    input_data = GetCreditEntryDetailsByIdInput(client_credit_id=client_credit_entry.id)

    result = use_case.execute(input_data)

    assert isinstance(result, CreditEntryDetailsOutput)
    print(result)

    assert result.vip_client_name == "Jhon Doe"
    assert result.admin_name is None
    assert result.source_id == client_credit_entry.source_id
    assert result.related_entry_id is None
    assert result.id == client_credit_entry.id
    assert result.source_type == ClientCreditSourceType.INDICATION.value
    assert result.quantity == 20
    assert result.reason == "Créditos referentes a indicação."
    # indication reason is hardcoded in entity
    assert result.created_at == client_credit_entry.created_at


def test_get_credit_entry_by_id_admin_added_type_success(
    make_vip_client, make_client_credit_entry, read_uow, write_uow, make_user
):
    admin = make_user(is_admin=True, username="JhonDoeAdmin")
    write_uow.users.create(admin)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_id=admin.id,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        quantity=20,
        reason="Teste de credito adicionado por admin",
    )
    write_uow.client_credit_entries.create(client_credit_entry)

    use_case = GetCreditEntryDetailsByIdUseCase(read_uow)
    input_data = GetCreditEntryDetailsByIdInput(client_credit_id=client_credit_entry.id)

    result = use_case.execute(input_data)

    assert isinstance(result, CreditEntryDetailsOutput)

    assert result.vip_client_name == "Jhon Doe"
    assert result.admin_name == "JhonDoeAdmin"
    assert result.source_id == admin.id
    assert result.related_entry_id is None
    assert result.id == client_credit_entry.id
    assert result.source_type == ClientCreditSourceType.ADDED_BY_ADMIN.value
    assert result.quantity == 20
    assert result.reason == "Teste de credito adicionado por admin"
    assert result.created_at == client_credit_entry.created_at


def test_get_credit_entry_by_id_reversed_by_admin_type_success(
    make_vip_client, make_client_credit_entry, read_uow, write_uow, make_user
):
    admin = make_user(is_admin=True, username="JhonDoeAdmin")
    write_uow.users.create(admin)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    original_client_credit_entry = make_client_credit_entry(vip_client_id=vip_client.id)
    write_uow.client_credit_entries.create(original_client_credit_entry)

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_id=admin.id,
        source_type=ClientCreditSourceType.REVERSED_BY_ADMIN,
        related_entry_id=original_client_credit_entry.id,
        quantity=20,
        reason="Teste de credito adicionado por admin",
    )
    write_uow.client_credit_entries.create(client_credit_entry)

    use_case = GetCreditEntryDetailsByIdUseCase(read_uow)
    input_data = GetCreditEntryDetailsByIdInput(client_credit_id=client_credit_entry.id)

    result = use_case.execute(input_data)

    assert isinstance(result, CreditEntryDetailsOutput)

    assert result.vip_client_name == "Jhon Doe"
    assert result.admin_name == "JhonDoeAdmin"
    assert result.related_entry_id == original_client_credit_entry.id
    assert result.source_id == admin.id
    assert result.id == client_credit_entry.id
    assert result.source_type == ClientCreditSourceType.REVERSED_BY_ADMIN.value
    assert result.quantity == -20
    assert result.reason == "Teste de credito adicionado por admin"
    assert result.created_at == client_credit_entry.created_at


def test_get_credit_entry_by_id_not_found(
    make_vip_client, make_client_credit_entry, read_uow, write_uow
):
    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.INDICATION,
        quantity=20,
    )
    # we do not persist client credit entry for this test

    use_case = GetCreditEntryDetailsByIdUseCase(read_uow)
    input_data = GetCreditEntryDetailsByIdInput(client_credit_id=client_credit_entry.id)

    with pytest.raises(CreditEntryNotFoundError):
        use_case.execute(input_data)


def test_get_credit_entry_by_id_vip_client_not_found(
    make_vip_client, make_client_credit_entry, read_uow, write_uow
):
    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    # we do not persist vip_client for this test

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.INDICATION,
        quantity=20,
    )
    write_uow.client_credit_entries.create(client_credit_entry)

    use_case = GetCreditEntryDetailsByIdUseCase(read_uow)
    input_data = GetCreditEntryDetailsByIdInput(client_credit_id=client_credit_entry.id)

    with pytest.raises(VipClientNotFoundError):
        use_case.execute(input_data)


def test_get_credit_entry_by_id_added_by_admin_admin_not_found(
    make_vip_client, make_client_credit_entry, read_uow, write_uow, make_user
):
    admin = make_user(is_admin=True, username="JhonDoeAdmin")
    # we do not persist admin for this test

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    client_credit_entry = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_id=admin.id,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        quantity=20,
        reason="Teste de credito adicionado por admin",
    )
    write_uow.client_credit_entries.create(client_credit_entry)

    use_case = GetCreditEntryDetailsByIdUseCase(read_uow)
    input_data = GetCreditEntryDetailsByIdInput(client_credit_id=client_credit_entry.id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)
