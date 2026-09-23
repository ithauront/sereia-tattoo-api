from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.types.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.infrastructure.sqlalchemy.models.appointments import AppointmentModel
from app.infrastructure.sqlalchemy.repositories.appointments_repository_sqlalchemy import (
    SQLAlchemyAppointmentsRepository,
)
from app.infrastructure.sqlalchemy.repositories.users_repository_sqlalchemy import (
    SQLAlchemyUsersRepository,
)
from app.infrastructure.sqlalchemy.repositories.vip_clients_repository_sqlalchemy import (
    SQLAlchemyVipClientsRepository,
)


def test_create_and_find_by_id(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    appointment = make_quoted_appointment(price=Decimal("700"), user_id=user.id)
    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None
    assert found.price == Decimal("700")
    assert found.status == AppointmentStatus.QUOTED


def test_find_many_by_project_id_returns_latest_session_first(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
    sqlalchemy_users_repo: SQLAlchemyUsersRepository,
    make_user,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)
    project_id = uuid4()

    first = make_quoted_appointment(
        user_id=user.id,
        project_id=project_id,
        current_session=1,
        total_sessions=3,
    )
    second = make_quoted_appointment(
        user_id=user.id,
        project_id=project_id,
        current_session=2,
        total_sessions=3,
    )
    another_project = make_quoted_appointment(
        user_id=user.id,
        project_id=uuid4(),
        current_session=1,
        total_sessions=2,
    )
    sqlalchemy_appointments_repo.create(first)
    sqlalchemy_appointments_repo.create(second)
    sqlalchemy_appointments_repo.create(another_project)

    found = sqlalchemy_appointments_repo.find_many_by_project_id(project_id)

    assert [appointment.id for appointment in found] == [second.id, first.id]


def test_find_overlap_excludes_selected_appointment_in_database_query(
    sqlalchemy_appointments_repo,
    sqlalchemy_users_repo,
    make_user,
    make_quoted_appointment,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)
    start_at = datetime(2030, 1, 1, 10, tzinfo=timezone.utc)
    excluded = make_quoted_appointment(
        user_id=user.id,
        start_at=start_at,
        end_at=start_at + timedelta(hours=2),
    )
    another_overlap = make_quoted_appointment(
        user_id=user.id,
        start_at=start_at + timedelta(hours=1),
        end_at=start_at + timedelta(hours=3),
    )
    sqlalchemy_appointments_repo.create(excluded)
    sqlalchemy_appointments_repo.create(another_overlap)

    result = sqlalchemy_appointments_repo.find_overlap(
        start_date=start_at,
        end_date=start_at + timedelta(hours=2),
        user_id=user.id,
        exclude_appointment_id=excluded.id,
    )

    assert [appointment.id for appointment in result] == [another_overlap.id]


def test_find_overlap_ignores_canceled_appointment_in_database_query(
    sqlalchemy_appointments_repo,
    sqlalchemy_users_repo,
    make_user,
    make_appointment_base,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)
    start_at = datetime(2030, 1, 1, 10, tzinfo=timezone.utc)
    canceled = make_appointment_base(
        user_id=user.id,
        status=AppointmentStatus.CANCELED,
        start_at=start_at,
        end_at=start_at + timedelta(hours=2),
    )
    sqlalchemy_appointments_repo.create(canceled)

    result = sqlalchemy_appointments_repo.find_overlap(
        start_date=start_at,
        end_date=start_at + timedelta(hours=2),
        user_id=user.id,
    )

    assert result == []


def test_db_constraint_rejects_invalid_client_info(
    db_session,
    make_user,
    sqlalchemy_users_repo,
):

    user = make_user()
    sqlalchemy_users_repo.create(user)

    now = datetime.now(timezone.utc)

    invalid = AppointmentModel(
        id=uuid4(),
        status=AppointmentStatus.REQUESTED,
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
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
    make_user,
    sqlalchemy_users_repo,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    appointment = make_quoted_appointment(price=Decimal("700"), user_id=user.id)
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
    make_user,
    sqlalchemy_users_repo,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip)

    appointment = make_quoted_appointment(client_info=ClientInfo(vip_client_id=vip.id), user_id=user.id)

    sqlalchemy_appointments_repo.create(appointment)

    found = sqlalchemy_appointments_repo.find_by_id(appointment.id)

    assert found is not None

    assert found.client_info.vip_client_id == vip.id
    assert found.client_info.name is None


def test_persists_non_vip_client_correctly(
    make_quoted_appointment,
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_user,
    sqlalchemy_users_repo,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    appointment = make_quoted_appointment(
        client_info=ClientInfo(
            vip_client_id=None,
            name="John Doe",
            email="john@doe.com",
            phone="71988888888",
        ),
        user_id=user.id,
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
    make_user,
    sqlalchemy_users_repo,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    vip = make_vip_client()
    sqlalchemy_vip_clients_repo.create(vip)

    appointment = make_quoted_appointment(
        client_info=ClientInfo(name="John Doe", email="jhon@doe.com", phone="71988888888"),
        user_id=user.id,
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
    make_user,
    sqlalchemy_users_repo,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    appointment1 = make_quoted_appointment(color=True, user_id=user.id)
    appointment2 = make_quoted_appointment(color=False, user_id=user.id)

    sqlalchemy_appointments_repo.create(appointment1)
    sqlalchemy_appointments_repo.create(appointment2)

    result = sqlalchemy_appointments_repo.find_many(color=True)

    assert len(result) == 1


def test_count_matches_find_many(
    sqlalchemy_appointments_repo: SQLAlchemyAppointmentsRepository,
    make_quoted_appointment,
    make_user,
    sqlalchemy_users_repo,
):
    user = make_user()
    sqlalchemy_users_repo.create(user)

    appointment1 = make_quoted_appointment(color=True, user_id=user.id)
    appointment2 = make_quoted_appointment(color=False, user_id=user.id)

    sqlalchemy_appointments_repo.create(appointment1)
    sqlalchemy_appointments_repo.create(appointment2)

    result_len = len(sqlalchemy_appointments_repo.find_many(color=True))

    total = sqlalchemy_appointments_repo.count_many(color=True)

    assert result_len == total
