from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from app.application.studio.use_cases.DTO.user_status_dto import DeactivateUserInput
from app.application.studio.use_cases.users_use_cases.deactivate_user import (
    DeactivateUserUseCase,
)
from app.core.exceptions.users import (
    CannotDeactivateYourselfError,
    LastAdminCannotBeDeactivatedError,
    UserNotFoundError,
)
from app.core.types.audit_actor_type import AuditActorType


def test_deactivate_user_success(write_uow, make_user):
    admin = make_user(
        is_active=True, is_admin=True, access_token_version=0, refresh_token_version=0
    )  # admin is verify in route but I prefer to explicit admin here
    user = make_user(is_active=True, has_activated_once=True)
    write_uow.users.create(admin)
    write_uow.users.create(user)

    use_case = DeactivateUserUseCase(write_uow)
    input_data = DeactivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_active is False
    assert user.has_activated_once is True
    assert user.access_token_version == 1
    assert user.refresh_token_version == 1


def test_deactivate_user_create_log(write_uow, make_user, read_uow):
    admin = make_user(
        is_active=True, is_admin=True, access_token_version=0, refresh_token_version=0
    )  # admin is verify in route but I prefer to explicit admin here
    user = make_user(is_active=True, has_activated_once=True)
    write_uow.users.create(admin)
    write_uow.users.create(user)

    use_case = DeactivateUserUseCase(write_uow)
    input_data = DeactivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")

    log = logs[0]

    assert log.entity_name == "users"
    assert log.entity_id == user.id
    assert log.action == "deactivate user"
    assert log.actor_id == admin.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {
        "is_active": {
            "from": True,
            "to": False,
        }
    }
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)


def test_cannot_deactivate_yourself(write_uow, make_user, read_uow):
    admin1 = make_user(is_admin=True, access_token_version=0, refresh_token_version=0)
    admin2 = make_user(is_admin=True)  # 2 admins to not mistake with last admin rule.

    write_uow.users.create(admin1)
    write_uow.users.create(admin2)

    use_case = DeactivateUserUseCase(write_uow)
    input_data = DeactivateUserInput(user_id=admin1.id, actor_id=admin1.id)

    with pytest.raises(CannotDeactivateYourselfError):
        use_case.execute(input_data)

    assert admin1.access_token_version == 0
    assert admin1.refresh_token_version == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []


def test_last_active_admin_cannot_be_deactivated(write_uow, make_user, read_uow):
    inactive_admin = make_user(
        is_admin=True, is_active=False
    )  # actor active verification is made in controller
    last_active_admin = make_user(is_admin=True)
    write_uow.users.create(inactive_admin)
    write_uow.users.create(last_active_admin)

    use_case = DeactivateUserUseCase(write_uow)
    input_data = DeactivateUserInput(
        user_id=last_active_admin.id, actor_id=inactive_admin.id
    )

    with pytest.raises(LastAdminCannotBeDeactivatedError):
        use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []


def test_user_not_found_to_deactivate(write_uow, make_user, read_uow):
    admin = make_user(is_active=True, is_admin=True)
    not_user_id = uuid4()
    write_uow.users.create(admin)

    use_case = DeactivateUserUseCase(write_uow)
    input_data = DeactivateUserInput(user_id=not_user_id, actor_id=admin.id)

    with pytest.raises(UserNotFoundError):
        use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []


def test_user_already_inactive(write_uow, make_user, read_uow):
    admin = make_user(is_active=True, is_admin=True)
    user = make_user(is_active=False)
    write_uow.users.create(admin)
    write_uow.users.create(user)

    use_case = DeactivateUserUseCase(write_uow)
    input_data = DeactivateUserInput(user_id=user.id, actor_id=admin.id)

    use_case.execute(input_data)

    assert user.is_active is False

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="users")
    assert logs == []
