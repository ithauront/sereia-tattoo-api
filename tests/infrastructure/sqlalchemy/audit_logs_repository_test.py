from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.types.audit_actor_type import AuditActorType


# TODO: testar um caso em se o auditlog falhar se faz rollback e não salva o caso original, por exemplo usando o usecase do addclientcreditby admin. não sei se esse teste deve ser nesse lugar, se não procurar onde é o luggar ideal. não é no teste do use_case pq ele usa fake repo
def test_create_and_find_many_by_entity_name(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    user = make_user()
    sqlalchemy_users_repo.create(user)

    for i in range(5):
        log = make_audit_log(
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
            actor_id=user.id,
        )
        sqlalchemy_audit_logs_repo.create(log)

    logs = sqlalchemy_audit_logs_repo.find_many_by_entity_name(entity_name="users")

    reason = [log.reason for log in logs]
    assert len(logs) == 5

    assert reason == [
        "client change his address4",
        "client change his address3",
        "client change his address2",
        "client change his address1",
        "client change his address0",
    ]


def test_actor_id_not_an_user_raises_error(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    log = make_audit_log(actor_id=uuid4())

    with pytest.raises(IntegrityError):
        sqlalchemy_audit_logs_repo.create(log)


def test_actor_id_can_be_nullable(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    log = make_audit_log(actor_id=None)

    sqlalchemy_audit_logs_repo.create(log)

    result = sqlalchemy_audit_logs_repo.find_many_by_entity_name(entity_name="users")

    assert result[0].actor_id is None
    assert result[0].entity_id == log.entity_id
    assert result[0].actor_id is None


def test_find_many_by_non_existent_actor_id(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    for i in range(5):
        log = make_audit_log(reason=f"client change his address{i}", actor_id=user.id)
        sqlalchemy_audit_logs_repo.create(log)

    result = sqlalchemy_audit_logs_repo.find_many_by_actor(actor_id=uuid4())

    assert result == []


def test_cannot_create_without_entity_id(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    log = make_audit_log(entity_id=None, actor_id=user.id)

    with pytest.raises(IntegrityError) as exc:
        sqlalchemy_audit_logs_repo.create(log)

    assert "NOT NULL constraint failed" in str(exc.value)


def test_actor_id_points_to_user_table(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    log = make_audit_log(actor_id=user.id)
    sqlalchemy_audit_logs_repo.create(log)

    log_found = sqlalchemy_audit_logs_repo.find_many_by_actor(actor_id=user.id)

    log_result = log_found[0]

    user_found = sqlalchemy_users_repo.find_by_id(log_result.actor_id)

    assert log_result.actor_id == user.id

    assert user_found.username == user.username


def test_pagination(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):

    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    user = make_user()
    sqlalchemy_users_repo.create(user)

    for i in range(5):
        log = make_audit_log(
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
            actor_id=user.id,
        )
        sqlalchemy_audit_logs_repo.create(log)

    result = sqlalchemy_audit_logs_repo.find_many_by_entity_name(
        entity_name="users",
        limit=2,
        offset=1,
    )

    # offset=1 skips first result
    assert len(result) == 2
    assert result[0].reason == "client change his address3"
    assert result[1].reason == "client change his address2"


def test_offset_over_total(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    user = make_user()
    sqlalchemy_users_repo.create(user)

    for i in range(5):
        log = make_audit_log(
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
            actor_id=user.id,
        )
        sqlalchemy_audit_logs_repo.create(log)

    result = sqlalchemy_audit_logs_repo.find_many_by_entity_name(
        entity_name="users",
        offset=6,
    )

    assert result == []


def test_persists_actor_type_enum(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    log = make_audit_log(actor_type=AuditActorType.SYSTEM, actor_id=user.id)

    sqlalchemy_audit_logs_repo.create(log)

    result = sqlalchemy_audit_logs_repo.find_many_by_entity_name(
        entity_name=log.entity_name
    )

    assert result[0].actor_type == AuditActorType.SYSTEM


def test_persists_changes_json(
    make_audit_log, sqlalchemy_audit_logs_repo, make_user, sqlalchemy_users_repo
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    log = make_audit_log(
        changes={"phone": {"from": "111", "to": "222"}}, actor_id=user.id
    )

    sqlalchemy_audit_logs_repo.create(log)

    result = sqlalchemy_audit_logs_repo.find_many_by_entity_id(log.entity_id)

    assert result[0].changes == {"phone": {"from": "111", "to": "222"}}
