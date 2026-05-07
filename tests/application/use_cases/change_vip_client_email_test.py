from datetime import datetime, timedelta, timezone

from pydantic import ValidationError
import pytest
from app.application.studio.use_cases.DTO.change_email_dto import (
    ChangeVipClientEmailInput,
)
from app.application.studio.use_cases.users_use_cases.change_vip_client_email import (
    ChangeVipClientEmailUseCase,
)
from app.core.exceptions.users import EmailAlreadyTakenError, VipClientNotFoundError
from app.core.types.audit_actor_type import AuditActorType


def test_vip_client_change_email_success(
    write_uow, read_uow, make_vip_client, make_user
):
    admin = make_user(is_admin=True)
    vip_client = make_vip_client(email="jhon@doe.com")
    write_uow.vip_clients.create(vip_client)

    use_case = ChangeVipClientEmailUseCase(write_uow)
    input_data = ChangeVipClientEmailInput(
        new_email="new@email.com", vip_client_id=vip_client.id, actor_id=admin.id
    )

    use_case.execute(input_data)

    saved = read_uow.vip_clients.find_by_id(vip_client.id)
    assert saved.email == "new@email.com"
    assert read_uow.vip_clients.find_by_email("jhon@doe.com") is None


def test_verify_log_created_success(write_uow, read_uow, make_vip_client, make_user):
    admin = make_user(is_admin=True)
    vip_client = make_vip_client(email="jhon@doe.com")
    write_uow.vip_clients.create(vip_client)

    use_case = ChangeVipClientEmailUseCase(write_uow)
    input_data = ChangeVipClientEmailInput(
        new_email="new@email.com", vip_client_id=vip_client.id, actor_id=admin.id
    )

    use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=admin.id)
    log = logs[0]

    assert log is not None
    assert log.entity_name == "users"
    assert log.entity_id == vip_client.id
    assert log.action == "change vip client email"
    assert log.actor_id == admin.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {
        "email": {
            "from": "jhon@doe.com",
            "to": "new@email.com",
        }
    }
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)


def test_vip_client_change_to_same_email_should_pass(
    write_uow, read_uow, make_vip_client, make_user
):
    admin = make_user(is_admin=True)
    vip_client = make_vip_client(email="jhon@doe.com")
    write_uow.vip_clients.create(vip_client)

    use_case = ChangeVipClientEmailUseCase(write_uow)
    input_data = ChangeVipClientEmailInput(
        new_email="jhon@doe.com", vip_client_id=vip_client.id, actor_id=admin.id
    )

    use_case.execute(input_data)

    saved = read_uow.vip_clients.find_by_id(vip_client.id)
    assert saved.email == "jhon@doe.com"

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=admin.id)
    assert logs == []


def test_vip_client_change_to_same_email_should_not_create_log(
    write_uow, read_uow, make_vip_client, make_user
):
    admin = make_user(is_admin=True)
    vip_client = make_vip_client(email="jhon@doe.com")
    write_uow.vip_clients.create(vip_client)

    use_case = ChangeVipClientEmailUseCase(write_uow)
    input_data = ChangeVipClientEmailInput(
        new_email="jhon@doe.com", vip_client_id=vip_client.id, actor_id=admin.id
    )

    use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=admin.id)
    assert logs == []


def test_email_is_normalized(write_uow, read_uow, make_vip_client, make_user):
    admin = make_user(is_admin=True)
    vip_client = make_vip_client(email="jhon@doe.com")
    write_uow.vip_clients.create(vip_client)

    use_case = ChangeVipClientEmailUseCase(write_uow)
    input_data = ChangeVipClientEmailInput(
        new_email="  New@Email.COM  ", vip_client_id=vip_client.id, actor_id=admin.id
    )

    use_case.execute(input_data)

    saved = read_uow.vip_clients.find_by_id(vip_client.id)
    assert saved.email == "new@email.com"


def test_vip_client_not_exists_change_email(
    write_uow, make_vip_client, make_user, read_uow
):
    admin = make_user(is_admin=True)
    vip_client = make_vip_client(email="jhon@doe.com")
    # vip_client not created in repo

    use_case = ChangeVipClientEmailUseCase(write_uow)
    input_data = ChangeVipClientEmailInput(
        new_email="jhon@doe.com", vip_client_id=vip_client.id, actor_id=admin.id
    )

    with pytest.raises(VipClientNotFoundError):
        use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=admin.id)
    assert logs == []


def test_vip_client_email_already_in_use(
    write_uow, read_uow, make_vip_client, make_user
):
    admin = make_user(is_admin=True)
    vip_client_1 = make_vip_client(email="jhon@doe.com")
    vip_client_2 = make_vip_client(email="jane@doe.com")
    write_uow.vip_clients.create(vip_client_1)
    write_uow.vip_clients.create(vip_client_2)

    use_case = ChangeVipClientEmailUseCase(write_uow)
    input_data = ChangeVipClientEmailInput(
        new_email="jane@doe.com", vip_client_id=vip_client_1.id, actor_id=admin.id
    )
    with pytest.raises(EmailAlreadyTakenError):
        use_case.execute(input_data)

    saved = read_uow.vip_clients.find_by_id(vip_client_1.id)
    assert saved.email == "jhon@doe.com"

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=admin.id)
    assert logs == []


def test_change_email_email_not_valid(make_vip_client, read_uow, make_user):
    # dto test
    admin = make_user(is_admin=True)
    vip_client = make_vip_client(email="jhon@doe.com")
    with pytest.raises(ValidationError):
        ChangeVipClientEmailInput(
            new_email="wrong_email_format",
            vip_client_id=vip_client.id,
            actor_id=admin.id,
        )

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=admin.id)
    assert logs == []
