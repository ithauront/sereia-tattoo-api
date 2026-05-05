from datetime import timedelta, datetime, timezone
from uuid import uuid4

import pytest

from app.core.types.audit_actor_type import AuditActorType
from tests.fakes.fake_audit_logs_repository import FakeAuditLogsRepository
from tests.fakes.fake_users_repository import FakeUsersRepository


@pytest.fixture
def logs_repo():
    return FakeAuditLogsRepository()


def test_create_and_find_many_by_entity_name(make_audit_log, logs_repo):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        log = make_audit_log(
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
        )
        logs_repo.create(log)

    logs = logs_repo.find_many_by_entity_name(entity_name="users")

    reason = [log.reason for log in logs]
    assert len(logs) == 5

    assert reason == [
        "client change his address4",
        "client change his address3",
        "client change his address2",
        "client change his address1",
        "client change his address0",
    ]


def test_find_many_by_actor(make_audit_log, logs_repo):
    user_id = uuid4()

    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        log = make_audit_log(
            actor_id=user_id,
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
        )
        logs_repo.create(log)

    logs = logs_repo.find_many_by_actor(actor_id=user_id)

    reason = [log.reason for log in logs]

    assert reason == [
        "client change his address4",
        "client change his address3",
        "client change his address2",
        "client change his address1",
        "client change his address0",
    ]


def test_find_many_with_offset_and_limit(
    logs_repo,
    make_audit_log,
):

    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        log = make_audit_log(
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
        )
        logs_repo.create(log)

    result = logs_repo.find_many_by_entity_name(
        entity_name="users",
        limit=2,
        offset=1,
    )

    # offset=1 skips first result
    assert len(result) == 2
    assert result[0].reason == "client change his address3"
    assert result[1].reason == "client change his address2"


def test_find_many_with_offset(
    logs_repo,
    make_audit_log,
):

    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        log = make_audit_log(
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
        )
        logs_repo.create(log)

    result = logs_repo.find_many_by_entity_name(
        entity_name="users",
        offset=1,
    )

    # offset=1 skips first result
    assert len(result) == 4
    assert result[0].reason == "client change his address3"
    assert result[1].reason == "client change his address2"
    assert result[2].reason == "client change his address1"
    assert result[3].reason == "client change his address0"


def test_find_many_returns_empty_when_offset_exceeds_len(
    logs_repo,
    make_audit_log,
):

    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        log = make_audit_log(
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
        )
        logs_repo.create(log)

    result = logs_repo.find_many_by_entity_name(
        entity_name="users",
        offset=6,
    )

    assert result == []


def test_find_many_with_limit(
    logs_repo,
    make_audit_log,
):

    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    for i in range(5):
        log = make_audit_log(
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
        )
        logs_repo.create(log)

    result = logs_repo.find_many_by_entity_name(
        entity_name="users",
        limit=2,
    )

    assert len(result) == 2
    assert result[0].reason == "client change his address4"
    assert result[1].reason == "client change his address3"


def test_find_many_by_returns_empty_if_no_logs_found(
    logs_repo,
):
    logs = logs_repo.find_many_by_entity_name(entity_name="users")

    assert logs == []


def test_find_many_by_entity_id(make_audit_log, logs_repo):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    correct_user_id = uuid4()
    wrong_user_id = uuid4()

    for i in range(5):
        log = make_audit_log(
            entity_name="users",
            entity_id=correct_user_id,
            actor_id=None,
            actor_type=AuditActorType.SYSTEM,
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
        )
        logs_repo.create(log)

    for i in range(2):
        outside_of_result_log = make_audit_log(
            entity_name="users",
            entity_id=wrong_user_id,
            actor_id=None,
            actor_type=AuditActorType.SYSTEM,
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
        )
        logs_repo.create(outside_of_result_log)

    logs = logs_repo.find_many_by_entity_id(correct_user_id)

    assert len(logs) == 5

    reason = [log.reason for log in logs]

    assert reason == [
        "client change his address4",
        "client change his address3",
        "client change his address2",
        "client change his address1",
        "client change his address0",
    ]

    assert logs[0].actor_type == AuditActorType.SYSTEM


def test_changes_correct_format(make_audit_log, logs_repo):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    correct_user_id = uuid4()

    for i in range(5):
        log = make_audit_log(
            entity_name="users",
            entity_id=correct_user_id,
            actor_id=None,
            actor_type=AuditActorType.SYSTEM,
            reason=f"client change his address{i}",
            performed_at=base_time + timedelta(hours=i),
            changes={"phone": {"from": "111", "to": "222"}},
        )
        logs_repo.create(log)

    logs = logs_repo.find_many_by_entity_id(correct_user_id)

    assert logs[0].changes == {"phone": {"from": "111", "to": "222"}}
