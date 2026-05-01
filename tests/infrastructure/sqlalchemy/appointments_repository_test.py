from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.core.types.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.infrastructure.sqlalchemy.models.appointments import AppointmentModel
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)


def test_create_and_find_by_id(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
):
    appointment = make_quoted_appointment(price=Decimal("700"))
    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None
    assert found.price == Decimal("700")
    assert found.status == AppointmentStatus.QUOTED


def test_db_constraint_rejects_invalid_client_info(db_session):
    now = datetime.now(timezone.utc)

    invalid = AppointmentModel(
        id=uuid4(),
        status=AppointmentStatus.REQUESTED,
        appointment_type=AppointmentType.TATTOO,
        start_at=now + timedelta(days=1),
        end_at=now + timedelta(days=1, hours=2),
        placement="ombro",
        details="teste",
        size=None,
        current_session=None,
        total_sessions=None,
        color=False,
        price=None,
        deposit_confirmed_at=None,
        vip_client_id=None,
        client_name=None,
        client_email=None,
        client_phone=None,
        referral_code=None,
        is_posted_on_socials=False,
        observations=None,
        created_at=now,
        updated_at=now,
    )

    db_session.add(invalid)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_update(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
):
    appointment = make_quoted_appointment(price=Decimal("700"))
    sqlalchemy_appointments_repo.create(appointment)

    before = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert before is not None
    assert before.price == Decimal("700")

    appointment.price = Decimal("100")
    sqlalchemy_appointments_repo.update(appointment)

    after = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert after is not None
    assert after.price == Decimal("100")


def test_persists_vip_client_correctly(
    make_vip_client,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    make_quoted_appointment,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
):
    vip = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip)

    appointment = make_quoted_appointment(client_info=ClientInfo(vip_client_id=vip.id))

    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None

    assert found.client_info.vip_client_id == vip.id
    assert found.client_info.name is None


def test_persists_non_vip_client_correctly(
    make_quoted_appointment,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
):
    appointment = make_quoted_appointment(
        client_info=ClientInfo(
            vip_client_id=None,
            name="John Doe",
            email="john@doe.com",
            phone="71988888888",
        )
    )

    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None

    assert found.client_info.name == "John Doe"
    assert found.client_info.vip_client_id is None


def test_update_switches_from_non_vip_to_vip(
    make_vip_client,
    sqlalchemy_vip_clients_repo: SQLAlchemyVipClientsRepository,
    make_quoted_appointment,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
):
    vip = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip)

    appointment = make_quoted_appointment(
        client_info=ClientInfo(
            name="John Doe", email="jhon@doe.com", phone="71988888888"
        )
    )
    sqlalchemy_appointments_repo.create(appointment)

    appointment.client_info = ClientInfo(vip_client_id=vip.id)

    sqlalchemy_appointments_repo.update(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None

    assert found.client_info.vip_client_id == vip.id
    assert found.client_info.name is None


def test_find_many_filters_by_color(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
):
    appointment1 = make_quoted_appointment(color=True)
    appointment2 = make_quoted_appointment(color=False)

    sqlalchemy_appointments_repo.create(appointment1)
    sqlalchemy_appointments_repo.create(appointment2)

    result = sqlalchemy_appointments_repo.find_many(color=True)

    assert len(result) == 1


def test_count_matches_find_many(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
):
    appointment1 = make_quoted_appointment(color=True)
    appointment2 = make_quoted_appointment(color=False)

    sqlalchemy_appointments_repo.create(appointment1)
    sqlalchemy_appointments_repo.create(appointment2)

    result_len = len(sqlalchemy_appointments_repo.find_many(color=True))

    total = sqlalchemy_appointments_repo.count_many(color=True)

    assert result_len == total
