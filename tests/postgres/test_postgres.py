from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.exc import DatabaseError, IntegrityError

from app.core.types.appointment_enums import AppointmentType
from app.infrastructure.sqlalchemy.models.appointments import AppointmentModel
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)


# TODO: testar o decimal no postgress
# TODO: verificar talvez outras coisas que devam ser testadas aqui; como o defaulte de false se não vira 0 e etc
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
