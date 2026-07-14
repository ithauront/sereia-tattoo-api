from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.studio.use_cases.DTO.commun import Direction
from app.core.types.appointment_enums import (
    AppointmentStatus,
    AppointmentType,
)
from app.domain.studio.appointments.entities.value_objects.client_info import (
    ClientInfo,
    NonVipContact,
)
from tests.fakes.fake_appointments_repository import FakeAppointmentsRepository
from tests.fakes.fake_users_repository import FakeUsersRepository
from tests.fakes.fake_vip_clients_repository import FakeVipClientsRepository


@pytest.fixture
def appointments_repo():
    return FakeAppointmentsRepository()


@pytest.fixture
def vip_client_repo():
    return FakeVipClientsRepository()


@pytest.fixture
def users_repo():
    return FakeUsersRepository()


def test_create_and_find_by_id(make_completed_appointment, appointments_repo, make_user, users_repo):
    user = make_user()
    users_repo.create(user)
    appointment = make_completed_appointment(user_id=user.id)

    appointments_repo.create(appointment)

    found = appointments_repo.find_by_id(appointment_id=appointment.id)

    assert found is not None
    assert found.status == AppointmentStatus.COMPLETED


def test_not_found_by_id(appointments_repo, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    found = appointments_repo.find_by_id(appointment_id=uuid4())

    assert found is None


def test_vip_client_in_client_info(
    vip_client_repo,
    make_completed_appointment,
    appointments_repo,
    make_vip_client,
    make_user,
    users_repo,
):
    user = make_user()
    users_repo.create(user)

    vip_client = make_vip_client()
    vip_client_repo.create(vip_client)

    appointment = make_completed_appointment(
        client_info=ClientInfo(vip_client_id=vip_client.id), user_id=user.id
    )
    appointments_repo.create(appointment)

    found = appointments_repo.find_by_id(appointment.id)

    assert found.client_info.is_vip is True
    assert found.client_info.matches_vip(vip_client.id) is True
    assert found.client_info.try_get_contact_info() is None


def test_non_vip_client_in_client_info(
    make_completed_appointment, appointments_repo, make_user, users_repo
):
    user = make_user()
    users_repo.create(user)

    appointment = make_completed_appointment(
        client_info=ClientInfo(
            vip_client_id=None,
            email="jhon@doe.com",
            name="Jhon Doe",
            phone="71988888888",
        ),
        user_id=user.id,
    )
    appointments_repo.create(appointment)

    found = appointments_repo.find_by_id(appointment.id)

    non_vip_contact_info = NonVipContact(email="jhon@doe.com", name="Jhon Doe", phone="71988888888")

    assert found.client_info.is_vip is False
    assert found.client_info.try_get_contact_info() == non_vip_contact_info


def test_update(appointments_repo, make_quoted_appointment, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    appointment = make_quoted_appointment(color=False, user_id=user.id)
    appointments_repo.create(appointment)

    before = appointments_repo.find_by_id(appointment.id)

    assert before is not None

    old_color = before.color

    appointment.color = True
    appointments_repo.update(appointment)

    after = appointments_repo.find_by_id(appointment.id)

    assert after is not None

    assert old_color is False
    assert after.color is True


def test_find_many_all_queries(appointments_repo, make_quoted_appointment, make_user, users_repo):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    user = make_user()
    users_repo.create(user)

    matching = make_quoted_appointment(
        start_at=base_time,
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        color=True,
        is_posted_on_socials=True,
        referral_code="JHON-BLUE",
    )

    appointments_repo.create(matching)

    for _ in range(5):
        appointments_repo.create(make_quoted_appointment(color=False, user_id=user.id))

    result = appointments_repo.find_many(
        start_date=base_time,
        end_date=base_time + timedelta(hours=1),
        status=matching.status,
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        color=True,
        is_posted_on_socials=True,
        referral_code="JHON-BLUE",
    )

    assert len(result) == 1
    assert result[0].id == matching.id


def test_find_many_exceeds_max_limit(appointments_repo, make_quoted_appointment, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    # Max_limit is 5000
    for _ in range(6000):
        appointments_repo.create(make_quoted_appointment(color=False, user_id=user.id))

    result = appointments_repo.find_many(color=False, limit=6000)

    assert len(result) == 5000


def test_find_many_partial_queries(appointments_repo, make_quoted_appointment, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    appointment1 = make_quoted_appointment(color=True, user_id=user.id)
    appointment2 = make_quoted_appointment(color=True, user_id=user.id)
    appointment3 = make_quoted_appointment(color=False, user_id=user.id)

    appointments_repo.create(appointment1)
    appointments_repo.create(appointment2)
    appointments_repo.create(appointment3)

    result = appointments_repo.find_many(
        color=True,
        appointment_type=AppointmentType.TATTOO,
    )

    assert len(result) == 2
    assert all(a.color for a in result)


def test_find_many_single_query(appointments_repo, make_quoted_appointment, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    appointment1 = make_quoted_appointment(color=True, user_id=user.id)
    appointment2 = make_quoted_appointment(color=False, user_id=user.id)

    appointments_repo.create(appointment1)
    appointments_repo.create(appointment2)

    result = appointments_repo.find_many(color=True)

    assert len(result) == 1
    assert result[0].color is True


def test_find_many_no_results(appointments_repo, make_quoted_appointment, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    appointments_repo.create(make_quoted_appointment(color=False, user_id=user.id))

    result = appointments_repo.find_many(color=True)

    assert result == []


def test_find_many_with_direction_offset_and_limit(
    appointments_repo, make_quoted_appointment, make_user, users_repo
):

    user = make_user()
    users_repo.create(user)

    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    appointments = []

    for i in range(5):
        appointment = make_quoted_appointment(start_at=base_time + timedelta(hours=i), user_id=user.id)
        appointment.created_at = base_time + timedelta(hours=i)
        appointments_repo.create(appointment)
        appointments.append(appointment)

    result_asc = appointments_repo.find_many(
        direction=Direction.asc,
        limit=2,
        offset=1,
    )

    # offset=1 skips first result
    assert len(result_asc) == 2
    assert result_asc[0].start_at == base_time + timedelta(hours=1)
    assert result_asc[1].start_at == base_time + timedelta(hours=2)

    result_desc = appointments_repo.find_many(
        direction=Direction.desc,
        limit=2,
        offset=1,
    )

    assert len(result_desc) == 2
    assert result_desc[0].start_at == base_time + timedelta(hours=3)
    assert result_desc[1].start_at == base_time + timedelta(hours=2)


def test_find_many_has_deposit_filter(
    appointments_repo, make_scheduled_appointment, make_quoted_appointment, make_user, users_repo
):
    user = make_user()
    users_repo.create(user)

    with_deposit = make_scheduled_appointment(user_id=user.id)
    without_deposit = make_quoted_appointment(user_id=user.id)

    appointments_repo.create(with_deposit)
    appointments_repo.create(without_deposit)

    result_true = appointments_repo.find_many(has_deposit=True)
    result_false = appointments_repo.find_many(has_deposit=False)

    assert len(result_true) == 1
    assert result_true[0].deposit_confirmed_at is not None

    assert len(result_false) == 1
    assert result_false[0].deposit_confirmed_at is None


def test_count_many_returns_correct_total(
    appointments_repo, make_quoted_appointment, make_user, users_repo
):
    user = make_user()
    users_repo.create(user)

    for _ in range(5):
        appointments_repo.create(make_quoted_appointment(user_id=user.id))

    result = appointments_repo.count_many()

    assert result == 5


def test_count_many_with_filter(appointments_repo, make_quoted_appointment, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    appointments_repo.create(make_quoted_appointment(color=True, user_id=user.id))
    appointments_repo.create(make_quoted_appointment(color=True, user_id=user.id))
    appointments_repo.create(make_quoted_appointment(color=False, user_id=user.id))

    result = appointments_repo.count_many(color=True)

    assert result == 2


def test_count_many_no_results(appointments_repo, make_quoted_appointment, make_user, users_repo):
    user = make_user()
    users_repo.create(user)

    appointments_repo.create(make_quoted_appointment(color=False, user_id=user.id))

    result = appointments_repo.count_many(color=True)

    assert result == 0


def test_count_matches_find_many(
    appointments_repo,
    make_quoted_appointment,
):
    for _ in range(3):
        appointments_repo.create(make_quoted_appointment(color=True))

    for _ in range(2):
        appointments_repo.create(make_quoted_appointment(color=False))

    count = appointments_repo.count_many(color=True)
    results = appointments_repo.find_many(color=True)

    assert count == len(results)


def test_find_overlap_has_overlap(appointments_repo, make_quoted_appointment, make_user, users_repo):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    end_time = base_time + timedelta(hours=5)

    query_start_time = base_time + timedelta(hours=3)
    query_end_time = base_time + timedelta(hours=7)

    user = make_user()
    users_repo.create(user)

    matching = make_quoted_appointment(
        start_at=base_time,
        end_at=end_time,
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        color=True,
        is_posted_on_socials=True,
        referral_code="JHON-BLUE",
    )

    appointments_repo.create(matching)

    result = appointments_repo.find_overlap(
        start_date=query_start_time, end_date=query_end_time, user_id=user.id
    )

    assert len(result) == 1
    assert result[0].id == matching.id


def test_find_overlap_does_not_overlap(
    appointments_repo, make_quoted_appointment, make_user, users_repo
):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    end_time = base_time + timedelta(hours=5)

    query_start_time = base_time + timedelta(hours=6)
    query_end_time = base_time + timedelta(hours=7)

    user = make_user()
    users_repo.create(user)

    matching = make_quoted_appointment(
        start_at=base_time,
        end_at=end_time,
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        color=True,
        is_posted_on_socials=True,
        referral_code="JHON-BLUE",
    )

    appointments_repo.create(matching)

    result = appointments_repo.find_overlap(
        start_date=query_start_time, end_date=query_end_time, user_id=user.id
    )

    assert len(result) == 0
    assert result == []


def test_find_overlap_touching_does_not_overlap(
    appointments_repo, make_quoted_appointment, make_user, users_repo
):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    end_time = base_time + timedelta(hours=5)

    query_start_time = base_time + timedelta(hours=5)
    query_end_time = base_time + timedelta(hours=7)

    user = make_user()
    users_repo.create(user)

    matching = make_quoted_appointment(
        start_at=base_time,
        end_at=end_time,
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        color=True,
        is_posted_on_socials=True,
        referral_code="JHON-BLUE",
    )

    appointments_repo.create(matching)

    result = appointments_repo.find_overlap(
        start_date=query_start_time, end_date=query_end_time, user_id=user.id
    )

    assert len(result) == 0
    assert result == []


def test_find_overlap_has_multiple_overlaps(
    appointments_repo, make_quoted_appointment, make_user, users_repo
):
    base_time = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    end_time = base_time + timedelta(hours=1)

    start_time_2 = base_time + timedelta(hours=2)
    end_time_2 = base_time + timedelta(hours=3)

    query_end_time = base_time + timedelta(hours=5)

    user = make_user()
    users_repo.create(user)

    matching_1 = make_quoted_appointment(
        start_at=base_time,
        end_at=end_time,
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        color=True,
        is_posted_on_socials=True,
        referral_code="JHON-BLUE",
    )

    appointments_repo.create(matching_1)

    matching_2 = make_quoted_appointment(
        start_at=start_time_2,
        end_at=end_time_2,
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        color=True,
        is_posted_on_socials=True,
        referral_code="JHON-BLUE",
    )

    appointments_repo.create(matching_2)

    result = appointments_repo.find_overlap(
        start_date=base_time, end_date=query_end_time, user_id=user.id
    )

    assert len(result) == 2
