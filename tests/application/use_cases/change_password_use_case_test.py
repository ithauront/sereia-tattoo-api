from datetime import datetime, timedelta, timezone

import pytest
from app.application.studio.use_cases.DTO.password_dto import ChangePasswordInput
from app.application.studio.use_cases.users_use_cases.change_password import (
    ChangePasswordUseCase,
)
from app.core.exceptions.users import AuthenticationFailedError
from app.core.security.passwords import verify_password
from app.core.types.audit_actor_type import AuditActorType


def test_change_password(write_uow, read_uow, make_user):
    user = make_user(
        password_token_version=0, access_token_version=0, refresh_token_version=0
    )
    write_uow.users.create(user)

    use_case = ChangePasswordUseCase(write_uow)
    input_data = ChangePasswordInput(
        user_id=user.id, old_password="123456", new_password="StrongPassword1"
    )

    old_hash = user.hashed_password

    use_case.execute(input_data)

    assert user.hashed_password != old_hash

    assert verify_password("StrongPassword1", user.hashed_password)

    saved = read_uow.users.find_by_id(user.id)
    assert verify_password("StrongPassword1", saved.hashed_password)
    assert saved.password_token_version == 1
    assert saved.access_token_version == 1
    assert saved.refresh_token_version == 1


def test_change_password_create_log(write_uow, read_uow, make_user):
    user = make_user(
        password_token_version=0, access_token_version=0, refresh_token_version=0
    )
    write_uow.users.create(user)

    use_case = ChangePasswordUseCase(write_uow)
    input_data = ChangePasswordInput(
        user_id=user.id, old_password="123456", new_password="StrongPassword1"
    )

    use_case.execute(input_data)

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    log = logs[0]

    assert log.entity_name == "users"
    assert log.entity_id == user.id
    assert log.action == "change user password"
    assert log.actor_id == user.id
    assert log.actor_type == AuditActorType.USER
    assert log.changes == {"password": {"change": True}}
    assert abs(log.performed_at - datetime.now(timezone.utc)) < timedelta(seconds=2)


def test_wrong_old_password(write_uow, make_user, read_uow):
    user = make_user(
        password_token_version=0, access_token_version=0, refresh_token_version=0
    )
    write_uow.users.create(user)

    use_case = ChangePasswordUseCase(write_uow)
    input_data = ChangePasswordInput(
        user_id=user.id, old_password="wrong_password", new_password="StrongPassword1"
    )

    with pytest.raises(AuthenticationFailedError):
        use_case.execute(input_data)

    assert user.password_token_version == 0
    assert user.access_token_version == 0
    assert user.refresh_token_version == 0

    logs = read_uow.audit_logs.find_many_by_actor(actor_id=user.id)
    assert logs == []
