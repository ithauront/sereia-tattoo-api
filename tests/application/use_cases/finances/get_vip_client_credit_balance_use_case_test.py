from uuid import uuid4

import pytest

from app.application.studio.use_cases.finances_use_cases.get_client_credit_balance import (
    GetClientCreditBalanceUseCase,
)
from app.core.exceptions.users import VipClientNotFoundError
from app.core.types.client_credit_source_type import ClientCreditSourceType


def test_get_vip_client_credits_balance_success(
    make_vip_client, make_client_credit_entry, read_uow, write_uow, make_user
):
    admin = make_user(is_admin=True, username="JhonDoeAdmin")
    write_uow.users.create(admin)

    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    for _ in range(10):
        client_credit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id,
            source_type=ClientCreditSourceType.INDICATION,
            quantity=10,
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    client_credit_entry_used = make_client_credit_entry(
        vip_client_id=vip_client.id,
        source_id=admin.id,
        source_type=ClientCreditSourceType.USED_IN_APPOINTMENT,
        quantity=20,
        reason="Teste de credito adicionado por admin",
    )
    write_uow.client_credit_entries.create(client_credit_entry_used)

    use_case = GetClientCreditBalanceUseCase(read_uow)

    result = use_case.execute(vip_client_id=vip_client.id)

    assert result == 80


def test_get_balance_vip_client_not_found(
    make_vip_client, make_client_credit_entry, read_uow, write_uow
):
    vip_client = make_vip_client(first_name="Jhon", last_name="Doe")
    write_uow.vip_clients.create(vip_client)

    for _ in range(10):
        client_credit_entry = make_client_credit_entry(
            vip_client_id=vip_client.id,
            source_type=ClientCreditSourceType.INDICATION,
            quantity=10,
        )
        write_uow.client_credit_entries.create(client_credit_entry)

    use_case = GetClientCreditBalanceUseCase(read_uow)

    with pytest.raises(VipClientNotFoundError):
        use_case.execute(vip_client_id=uuid4())


def test_get_balance_returns_zero_when_client_has_no_entries(make_vip_client, read_uow, write_uow):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    use_case = GetClientCreditBalanceUseCase(read_uow)

    result = use_case.execute(vip_client.id)

    assert result == 0
