import pytest

from app.application.studio.use_cases.DTO.add_client_credits import (
    AddClientCreditByAdminInput,
)
from app.application.studio.use_cases.finances_use_cases.add_client_credit_by_admin import (
    AddClientCreditByAdminUseCase,
)


def test_add_credits_rollback_if_audit_log_fails(
    sqlalchemy_write_uow,
    make_user,
    make_vip_client,
    mocker,
):
    # we will use the add client credit use case as base to test the rollback
    admin = make_user(email="admin@admin.com")
    vip_client = make_vip_client()

    sqlalchemy_write_uow.vip_clients.create(vip_client)

    use_case = AddClientCreditByAdminUseCase(sqlalchemy_write_uow)

    input_data = AddClientCreditByAdminInput(
        actor_id=admin.id,
        quantity=10,
        reason="test rollback",
        vip_client_id=vip_client.id,
    )

    mocker.patch.object(
        sqlalchemy_write_uow.audit_logs,
        "create",
        side_effect=Exception("audit log failed"),
    )

    with pytest.raises(Exception, match="audit log failed"):
        use_case.execute(input_data)

    credits = sqlalchemy_write_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )

    logs = sqlalchemy_write_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )

    assert credits == []
    assert logs == []
