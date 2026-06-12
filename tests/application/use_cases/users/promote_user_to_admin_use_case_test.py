from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.studio.use_cases.DTO.user_status_dto import PromoteUserInput
from app.application.studio.use_cases.users_use_cases.promote_user_to_admin import (
    PromoteUserToAdminUseCase,
)
from app.core.exceptions.users import UserNotFoundError
from app.core.types.audit_actor_type import AuditActorType


def test_promote_user_success(write_uow, make_user):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    user = make_user(is_active=True, is_admin=False)

    write_uow.users.create(user)

    use_case = PromoteUserToAdminUseCase(write_uow)
    input_data = PromoteUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_admin is True


def test_promote_user_create_log(write_uow, make_user, read_uow):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    user = make_user(is_active=True, is_admin=False)

    write_uow.users.create(user)

    use_case = PromoteUserToAdminUseCase(write_uow)
    input_data = PromoteUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")

    log = logs[0]

    assert log.entity_name == "users"
    assert log.entity_id == user.id
    assert log.action == "promote user to admin"
    assert log.actor_id == admin.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {
        "is_admin": {
            "from": False,
            "to": True,
        }
    }
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)


def test_user_not_found_to_promote(write_uow, make_user, read_uow):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    not_user_id = uuid4()

    use_case = PromoteUserToAdminUseCase(write_uow)
    input_data = PromoteUserInput(user_id=not_user_id, actor_id=admin.id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []


def test_user_already_admin(write_uow, make_user, read_uow):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    user = make_user(is_active=True, is_admin=True)

    write_uow.users.create(user)

    use_case = PromoteUserToAdminUseCase(write_uow)
    input_data = PromoteUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_admin is True

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []
