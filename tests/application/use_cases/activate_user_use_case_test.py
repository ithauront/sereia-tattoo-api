from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from app.application.studio.use_cases.DTO.user_status_dto import ActivateUserInput
from app.application.studio.use_cases.users_use_cases.activate_user import (
    ActivateUserUseCase,
)
from app.core.exceptions.users import UserNotFoundError
from app.core.types.audit_actor_type import AuditActorType


def test_activate_user_success(write_uow, make_user, read_uow):
    admin = make_user(is_admin=True, email="admin@admin.com")
    user = make_user(is_active=False)

    write_uow.users.create(user)
    assert user.has_activated_once is False

    use_case = ActivateUserUseCase(write_uow)
    input_data = ActivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_active is True
    assert user.has_activated_once is True


def test_activate_user_create_log(write_uow, make_user, read_uow):
    admin = make_user(is_admin=True, email="admin@admin.com")
    user = make_user(is_active=False)

    write_uow.users.create(user)
    assert user.has_activated_once is False

    use_case = ActivateUserUseCase(write_uow)
    input_data = ActivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")

    log = logs[0]

    assert log.entity_name == "users"
    assert log.entity_id == user.id
    assert log.action == "activate user"
    assert log.actor_id == admin.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {
        "is_active": {
            "from": False,
            "to": True,
        }
    }
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)


def reactivate_inactive_user_that_has_been_activated_once_success(
    write_uow, make_user, read_uow
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    user = make_user(is_active=False, has_activated_once=True)

    write_uow.users.create(user)
    assert user.has_activated_once is True

    use_case = ActivateUserUseCase(write_uow)
    input_data = ActivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")

    assert user.is_active is True
    assert user.has_activated_once is True

    assert len(logs) == 1


def test_user_not_found_to_activate(write_uow, read_uow, make_user):
    admin = make_user(is_admin=True, email="admin@admin.com")
    not_user_id = uuid4()

    use_case = ActivateUserUseCase(write_uow)
    input_data = ActivateUserInput(user_id=not_user_id, actor_id=admin.id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []


def test_user_already_active(write_uow, make_user, read_uow):
    admin = make_user(is_admin=True, email="admin@admin.com")
    user = make_user(is_active=True)

    write_uow.users.create(user)

    use_case = ActivateUserUseCase(write_uow)
    input_data = ActivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_active is True

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []
