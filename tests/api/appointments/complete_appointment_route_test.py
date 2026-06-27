from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.dependencies.events import get_transactional_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.types.appointment_enums import AppointmentStatus
from app.main import app

client = TestClient(app)


def test_complete_appointment_route_success(
    make_user,
    make_token,
    make_payment,
    make_scheduled_appointment,
    write_uow,
    read_uow,
    fake_transactional_event_bus,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

    appointment = make_scheduled_appointment(price=Decimal("700"), user_id=admin.id)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal("700"))
    write_uow.payments.create(payment)

    app.dependency_overrides[get_transactional_event_bus] = lambda: fake_transactional_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)
    assert appointment_in_repo.status == AppointmentStatus.COMPLETED

    logs = read_uow.audit_logs.find_many_by_entity_name(entity_name="appointments")
    assert len(logs) == 1

    app.dependency_overrides = {}


def test_complete_appointment_route_double_call(
    make_user,
    make_token,
    make_payment,
    make_scheduled_appointment,
    write_uow,
    read_uow,
    fake_transactional_event_bus,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

    appointment = make_scheduled_appointment(price=Decimal("700"), user_id=admin.id)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal("700"))
    write_uow.payments.create(payment)

    app.dependency_overrides[get_transactional_event_bus] = lambda: fake_transactional_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    first_call = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first_call.status_code == 204

    second_call = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second_call.status_code == 409
    assert second_call.json()["detail"] == "only_appointments_in_scheduled_status_can_be_completed"

    app.dependency_overrides = {}


def test_complete_appointment_not_scheduled(
    make_user,
    make_token,
    make_payment,
    make_quoted_appointment,
    write_uow,
    read_uow,
    fake_transactional_event_bus,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

    appointment = make_quoted_appointment(user_id=admin.id)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal("700"))
    write_uow.payments.create(payment)

    app.dependency_overrides[get_transactional_event_bus] = lambda: fake_transactional_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "only_appointments_in_scheduled_status_can_be_completed"

    app.dependency_overrides = {}


def test_complete_appointment_not_found(
    make_user,
    make_token,
    make_payment,
    make_scheduled_appointment,
    write_uow,
    read_uow,
    fake_transactional_event_bus,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

    appointment = make_scheduled_appointment(price=Decimal("700"), user_id=admin.id)
    # we do not persist appointment for this test

    payment = make_payment(appointment_id=appointment.id, amount=Decimal("700"))
    write_uow.payments.create(payment)

    app.dependency_overrides[get_transactional_event_bus] = lambda: fake_transactional_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "appointment_not_found"

    app.dependency_overrides = {}


def test_complete_appointment_not_fully_paid(
    make_user,
    make_token,
    make_payment,
    make_scheduled_appointment,
    write_uow,
    read_uow,
    fake_transactional_event_bus,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

    appointment = make_scheduled_appointment(price=Decimal("700"), user_id=admin.id)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal("100"))
    # payment is less than price
    write_uow.payments.create(payment)

    app.dependency_overrides[get_transactional_event_bus] = lambda: fake_transactional_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert (
        response.json()["detail"] == "appointment_was_not_fully_paid_check_payments_and_possible_refunds"
    )

    app.dependency_overrides = {}


def test_complete_appointment_not_admin(
    make_user,
    make_token,
    make_payment,
    make_scheduled_appointment,
    write_uow,
    read_uow,
    fake_transactional_event_bus,
):
    admin = make_user(is_admin=False, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

    appointment = make_scheduled_appointment(price=Decimal("700"), user_id=admin.id)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal("700"))
    write_uow.payments.create(payment)

    app.dependency_overrides[get_transactional_event_bus] = lambda: fake_transactional_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204
    # evry user -admin or not) can complete an appointment user != client

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)
    assert appointment_in_repo.status == AppointmentStatus.COMPLETED

    app.dependency_overrides = {}


def test_complete_appointment_inactive_admin(
    make_user,
    make_token,
    make_payment,
    make_scheduled_appointment,
    write_uow,
    read_uow,
    fake_transactional_event_bus,
):
    admin = make_user(is_admin=True, is_active=False, email="admin@admin.com")
    write_uow.users.create(admin)
    token = make_token(admin)

    appointment = make_scheduled_appointment(price=Decimal("700"), user_id=admin.id)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal("700"))
    write_uow.payments.create(payment)

    app.dependency_overrides[get_transactional_event_bus] = lambda: fake_transactional_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)
    assert appointment_in_repo.status == AppointmentStatus.SCHEDULED

    app.dependency_overrides = {}


def test_complete_appointment_non_existent_user(
    make_user,
    make_token,
    make_payment,
    make_scheduled_appointment,
    write_uow,
    read_uow,
    fake_transactional_event_bus,
):
    admin = make_user(is_admin=True, is_active=True, email="admin@admin.com")
    # we do not persist user for this test
    token = make_token(admin)

    appointment = make_scheduled_appointment(price=Decimal("700"), user_id=admin.id)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal("700"))
    write_uow.payments.create(payment)

    app.dependency_overrides[get_transactional_event_bus] = lambda: fake_transactional_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)
    assert appointment_in_repo.status == AppointmentStatus.SCHEDULED

    app.dependency_overrides = {}
