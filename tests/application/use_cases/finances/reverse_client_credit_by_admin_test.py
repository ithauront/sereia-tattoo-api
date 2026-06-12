import pytest

from app.application.studio.use_cases.DTO.reverse_client_credits import (
    ReverseClientCreditByAdminInput,
    ReverseClientCreditByAdminOutput,
)
from app.application.studio.use_cases.finances_use_cases.reverse_client_credit_by_admin import (
    ReverseClientCreditByAdminUseCase,
)
from app.core.exceptions.marketing import (
    CannotReverseNegativeEntryError,
    CreditAlreadyReversedError,
    CreditEntryNotFoundError,
)
from app.core.exceptions.users import VipClientNotFoundError
from app.core.types.audit_actor_type import AuditActorType
from app.core.types.client_credit_source_type import ClientCreditSourceType


def test_reverse_credits_success(
    write_uow, read_uow, make_user, make_vip_client, make_client_credit_entry
):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credits = make_client_credit_entry(vip_client_id=vip_client.id)
    write_uow.client_credit_entries.create(original_credits)

    use_case = ReverseClientCreditByAdminUseCase(write_uow)
    input_data = ReverseClientCreditByAdminInput(
        actor_id=admin.id,
        reason="to test use case",
        vip_client_id=vip_client.id,
        credit_id=original_credits.id,
    )

    result = use_case.execute(input_data)

    credits_saved = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    assert len(credits_saved) == 2  # original and reversed

    assert result.before == 10
    assert result.after == 0

    assert credits_saved[0].related_entry_id == original_credits.id
    assert credits_saved[0].quantity == -10
    assert credits_saved[0].reason == "to test use case"
    assert credits_saved[0].source_type == ClientCreditSourceType.REVERSED_BY_ADMIN


def test_reverse_credits_two_times_error(
    write_uow, make_user, make_vip_client, make_client_credit_entry, read_uow
):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credits = make_client_credit_entry(vip_client_id=vip_client.id)
    write_uow.client_credit_entries.create(original_credits)

    use_case = ReverseClientCreditByAdminUseCase(write_uow)
    input_data = ReverseClientCreditByAdminInput(
        actor_id=admin.id,
        reason="to test use case",
        vip_client_id=vip_client.id,
        credit_id=original_credits.id,
    )

    first_call = use_case.execute(input_data)
    assert isinstance(first_call, ReverseClientCreditByAdminOutput)

    with pytest.raises(CreditAlreadyReversedError):
        use_case.execute(input_data)

    balance = read_uow.client_credit_entries.get_balance(vip_client_id=vip_client.id)

    assert balance == 0  # created and reversed == 0 second call does not change balance


def test_reverse_client_credit_creates_correct_audit_log(
    write_uow, read_uow, make_user, make_vip_client, make_client_credit_entry
):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credits = make_client_credit_entry(vip_client_id=vip_client.id)
    write_uow.client_credit_entries.create(original_credits)

    use_case = ReverseClientCreditByAdminUseCase(write_uow)
    input_data = ReverseClientCreditByAdminInput(
        actor_id=admin.id,
        reason="to test use case",
        vip_client_id=vip_client.id,
        credit_id=original_credits.id,
    )

    use_case.execute(input_data)

    log = read_uow.audit_logs.find_many_by_entity_name(entity_name="client_credit_entry")

    assert log is not None
    assert len(log) == 1
    assert log[0].entity_name == "client_credit_entry"
    assert log[0].action == "admin reverse credits"
    assert log[0].actor_id == admin.id
    assert log[0].actor_type == AuditActorType.USER
    assert log[0].changes == {
        "balance": {
            "from": 10,
            "to": 0,
        },
        "credit": {
            "source_type": ClientCreditSourceType.REVERSED_BY_ADMIN,
            "quantity": -10,
            "original_credit": original_credits.id,
        },
        "vip_client": {
            "id": vip_client.id,
            "client_code": vip_client.client_code,
        },
    }
    assert log[0].reason == "to test use case"


def test_reverse_credits_vip_client_not_found(
    write_uow, read_uow, make_user, make_vip_client, make_client_credit_entry
):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    # we do not persist vip client for this test

    original_credits = make_client_credit_entry(vip_client_id=vip_client.id)
    write_uow.client_credit_entries.create(original_credits)

    use_case = ReverseClientCreditByAdminUseCase(write_uow)
    input_data = ReverseClientCreditByAdminInput(
        actor_id=admin.id,
        reason="to test use case",
        vip_client_id=vip_client.id,
        credit_id=original_credits.id,
    )

    with pytest.raises(VipClientNotFoundError):
        use_case.execute(input_data)


def test_reverse_non_existent_credits_error(
    write_uow, read_uow, make_user, make_vip_client, make_client_credit_entry
):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credits = make_client_credit_entry(vip_client_id=vip_client.id)
    # we do not persist credits for this test

    use_case = ReverseClientCreditByAdminUseCase(write_uow)
    input_data = ReverseClientCreditByAdminInput(
        actor_id=admin.id,
        reason="to test use case",
        vip_client_id=vip_client.id,
        credit_id=original_credits.id,
    )

    with pytest.raises(CreditEntryNotFoundError):
        use_case.execute(input_data)


def test_reverse_negative_credits_error(
    write_uow, read_uow, make_user, make_vip_client, make_client_credit_entry
):
    admin = make_user(email="admin@admin.com")
    write_uow.users.create(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    original_credits = make_client_credit_entry(
        vip_client_id=vip_client.id, source_type=ClientCreditSourceType.USED_IN_APPOINTMENT
    )
    write_uow.client_credit_entries.create(original_credits)

    use_case = ReverseClientCreditByAdminUseCase(write_uow)
    input_data = ReverseClientCreditByAdminInput(
        actor_id=admin.id,
        reason="to test use case",
        vip_client_id=vip_client.id,
        credit_id=original_credits.id,
    )

    with pytest.raises(CannotReverseNegativeEntryError):
        use_case.execute(input_data)
