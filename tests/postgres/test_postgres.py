from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import DatabaseError, IntegrityError

from app.core.types.appointment_enums import AppointmentType
from app.infrastructure.sqlalchemy.models.appointments import AppointmentModel
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.audit_logs_repository import (
    SQLAlchemyAuditLogsRepository,
)


def test_datetime_timezone_is_preserved(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
):
    start = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    appointment = make_quoted_appointment(
        start_at=start,
        end_at=end,
    )

    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None

    assert found.start_at.tzinfo is not None
    assert found.start_at == start


def test_timezone_is_utc_normalized(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
):
    start = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    appointment = make_quoted_appointment(start_at=start)
    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None
    offset = found.start_at.utcoffset()
    assert offset is not None
    assert offset.total_seconds() == 0


def test_color_default_to_false(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_appointment_base,
):
    appointment = make_appointment_base(color=None)

    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None

    assert found.color is False


def test_posted_on_socials_default_to_false(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_appointment_base,
):
    appointment = make_appointment_base(is_posted_on_socials=None)

    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None

    assert found.is_posted_on_socials is False


def test_db_rejects_invalid_status_enum_check(db_session):
    now = datetime.now(timezone.utc)

    invalid = AppointmentModel(
        id=uuid4(),
        status="INVALID",
        appointment_type=AppointmentType.TATTOO,
        start_at=now,
        end_at=now + timedelta(hours=1),
        placement="x",
        details="x",
        created_at=now,
        updated_at=now,
    )

    db_session.add(invalid)

    with pytest.raises((DatabaseError, IntegrityError)):
        db_session.flush()


def test_numeric_decimal_precision_is_preserved(
    sqlalchemy_appointments_repo,
    make_quoted_appointment,
):
    appointment = make_quoted_appointment(price=Decimal("10.50"))

    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None

    assert found.price == Decimal("10.50")
    assert isinstance(found.price, Decimal)


def test_json_persistence_in_postgress(
    sqlalchemy_audit_logs_repo: SQLAlchemyAuditLogsRepository, make_audit_log
):
    payload = {"phone": {"from": "111", "to": "222"}}
    log = make_audit_log(actor_id=None, changes=payload)
    sqlalchemy_audit_logs_repo.create(log)

    result = sqlalchemy_audit_logs_repo.find_many_by_entity_id(log.entity_id)

    assert result[0].changes == {"phone": {"from": "111", "to": "222"}}


def test_session_recovers_after_rollback(
    db_session, sqlalchemy_appointments_repo, make_quoted_appointment
):
    now = datetime.now(timezone.utc)

    invalid = AppointmentModel(
        id=uuid4(),
        status="INVALID",
        appointment_type=AppointmentType.TATTOO,
        start_at=now,
        end_at=now + timedelta(hours=1),
        placement="x",
        details="x",
        created_at=now,
        updated_at=now,
    )

    db_session.add(invalid)

    with pytest.raises((DatabaseError, IntegrityError)):
        db_session.flush()

    db_session.rollback()

    valid = make_quoted_appointment()

    sqlalchemy_appointments_repo.create(valid)

    found = sqlalchemy_appointments_repo.find_by_id(valid.id)

    assert found is not None
