from datetime import timedelta

import pytest

from app.application.studio.use_cases.DTO.add_client_credits import (
    AddClientCreditByAdminInput,
)
from app.application.studio.use_cases.finances_use_cases.add_client_credit_by_admin import (
    AddClientCreditByAdminUseCase,
)
from app.core.exceptions.marketing import CreditMustBePositiveError
from app.core.exceptions.users import VipClientNotFoundError
from app.core.types.audit_actor_type import AuditActorType
from app.core.types.client_credit_source_type import ClientCreditSourceType


def test_add_credits_success(write_uow, read_uow, make_user, make_vip_client):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    use_case = AddClientCreditByAdminUseCase(write_uow)

    input_data = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=10,
        reason="test adding credits",
        vip_client_id=vip_client.id,
    )

    result = use_case.execute(input_data)

    credit_saved = read_uow.client_credit_entries.find_many_by_vip_client_id(vip_client_id=vip_client.id)

    assert result.before == 0
    assert result.after == 10

    assert credit_saved is not None
    assert len(credit_saved) == 1
    assert credit_saved[0].reason == "test adding credits"
    assert credit_saved[0].source_id == admin.id
    assert credit_saved[0].source_type == "added_by_admin"


def test_add_credits_two_times_success(write_uow, read_uow, make_user, make_vip_client):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    use_case = AddClientCreditByAdminUseCase(write_uow)

    input_data_1 = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=10,
        reason="test adding credits1",
        vip_client_id=vip_client.id,
    )

    input_data_2 = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=10,
        reason="test adding credits2",
        vip_client_id=vip_client.id,
    )

    first_call = use_case.execute(input_data_1)

    second_call = use_case.execute(input_data_2)

    credit_saved = read_uow.client_credit_entries.find_many_by_vip_client_id(vip_client_id=vip_client.id)

    balance = read_uow.client_credit_entries.get_balance(vip_client_id=vip_client.id)

    assert first_call.before == 0
    assert first_call.after == 10

    assert second_call.before == 10
    assert second_call.after == 20

    assert balance == 20
    assert len(credit_saved) == 2

    assert credit_saved[0].reason == "test adding credits2"
    assert credit_saved[1].reason == "test adding credits1"


def test_add_credits_generate_correct_logs(write_uow, read_uow, make_user, make_vip_client):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    use_case = AddClientCreditByAdminUseCase(write_uow)

    input_data_1 = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=10,
        reason="test adding credits1",
        vip_client_id=vip_client.id,
    )

    input_data_2 = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=10,
        reason="test adding credits2",
        vip_client_id=vip_client.id,
    )

    use_case.execute(input_data_1)

    use_case.execute(input_data_2)

    credit_saved = read_uow.client_credit_entries.find_many_by_vip_client_id(vip_client_id=vip_client.id)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert logs is not None
    assert len(logs) == 2
    assert logs[0].entity_name == "client_credit_entry"
    assert logs[0].entity_id == credit_saved[0].id
    # both list are order in the same direction
    assert logs[0].action == "admin added credits"
    assert logs[0].actor_id == admin.id
    assert logs[0].actor_type == AuditActorType.USER
    assert logs[0].changes == {
        "balance": {
            "from": 10,
            "to": 20,
        },
        "credit": {
            "source_type": ClientCreditSourceType.ADDED_BY_ADMIN,
            "quantity": 10,
        },
        "vip_client": {
            "id": vip_client.id,
            "client_code": vip_client.client_code,
        },
    }
    # logs is order with must recent first
    assert logs[0].reason == "test adding credits2"
    assert abs(logs[0].performed_at - credit_saved[0].created_at) < timedelta(seconds=2)

    assert logs[1].entity_id == credit_saved[1].id
    assert logs[1].changes == {
        "balance": {
            "from": 0,
            "to": 10,
        },
        "credit": {
            "source_type": ClientCreditSourceType.ADDED_BY_ADMIN,
            "quantity": 10,
        },
        "vip_client": {
            "id": vip_client.id,
            "client_code": vip_client.client_code,
        },
    }
    assert logs[1].reason == "test adding credits1"
    assert abs(logs[1].performed_at - credit_saved[1].created_at) < timedelta(seconds=2)


def test_add_credits_vip_client_not_found(write_uow, read_uow, make_user, make_vip_client):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client()
    # we do not persist vip client for this test

    use_case = AddClientCreditByAdminUseCase(write_uow)

    input_data = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=10,
        reason="test adding credits",
        vip_client_id=vip_client.id,
    )

    with pytest.raises(VipClientNotFoundError):
        use_case.execute(input_data)

    credit_saved = read_uow.client_credit_entries.find_many_by_source_id(source_id=admin.id)

    assert credit_saved == []


def test_add_zero_credits_raises_error(write_uow, read_uow, make_user, make_vip_client):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    use_case = AddClientCreditByAdminUseCase(write_uow)

    input_data = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=0,
        reason="test adding credits",
        vip_client_id=vip_client.id,
    )

    with pytest.raises(CreditMustBePositiveError):
        use_case.execute(input_data)

    credit_saved = read_uow.client_credit_entries.find_many_by_source_id(source_id=admin.id)

    assert credit_saved == []


def test_add_negative_credits_raises_error(write_uow, read_uow, make_user, make_vip_client):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    use_case = AddClientCreditByAdminUseCase(write_uow)

    input_data = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=-10,
        reason="test adding credits",
        vip_client_id=vip_client.id,
    )

    with pytest.raises(CreditMustBePositiveError):
        use_case.execute(input_data)

    credit_saved = read_uow.client_credit_entries.find_many_by_source_id(source_id=admin.id)

    assert credit_saved == []
