from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.events import get_integration_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.types.appointment_enums import AppointmentStatus
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides = {}


def _override_dependencies(write_uow, read_uow, integration_bus):
    app.dependency_overrides[get_integration_event_bus] = lambda: integration_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow


def test_cancel_appointment_route_success(
    make_user,
    make_token,
    make_appointment_base,
    write_uow,
    read_uow,
    fake_integration_event_bus,
):
    owner = make_user()
    write_uow.users.create(owner)
    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)
    _override_dependencies(write_uow, read_uow, fake_integration_event_bus)

    response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={"reason": "Cliente solicitou o cancelamento"},
        headers={"Authorization": f"Bearer {make_token(owner)}"},
    )

    assert response.status_code == 204
    assert response.content == b""
    assert appointment.status == AppointmentStatus.CANCELED
    assert "Cliente solicitou o cancelamento" in (appointment.observations or "")
    assert len(fake_integration_event_bus.events) == 1


def test_cancel_appointment_route_returns_not_found(
    make_user,
    make_token,
    write_uow,
    read_uow,
    fake_integration_event_bus,
):
    user = make_user()
    write_uow.users.create(user)
    _override_dependencies(write_uow, read_uow, fake_integration_event_bus)

    response = client.patch(
        f"/appointments/{uuid4()}/cancel",
        json={"reason": "Appointment inexistente"},
        headers={"Authorization": f"Bearer {make_token(user)}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "appointment_not_found"}
    assert fake_integration_event_bus.events == []


def test_cancel_appointment_route_forbids_another_user(
    make_user,
    make_token,
    make_appointment_base,
    write_uow,
    read_uow,
    fake_integration_event_bus,
):
    owner = make_user()
    another_user = make_user()
    write_uow.users.create(owner)
    write_uow.users.create(another_user)
    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)
    _override_dependencies(write_uow, read_uow, fake_integration_event_bus)

    response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={"reason": "Tentativa sem autorização"},
        headers={"Authorization": f"Bearer {make_token(another_user)}"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "unauthorized_user"}
    assert appointment.status == AppointmentStatus.REQUESTED


@pytest.mark.parametrize(
    ("reason", "detail"),
    [
        ("   ", "cancellation_reason_required"),
        ("abc", "cancellation_reason_must_have_at_least_5_characters"),
        ("12345", "cancellation_reason_must_contain_letters"),
    ],
)
def test_cancel_appointment_route_translates_reason_validation_errors(
    reason,
    detail,
    make_user,
    make_token,
    make_appointment_base,
    write_uow,
    read_uow,
    fake_integration_event_bus,
):
    owner = make_user()
    write_uow.users.create(owner)
    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)
    _override_dependencies(write_uow, read_uow, fake_integration_event_bus)

    response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={"reason": reason},
        headers={"Authorization": f"Bearer {make_token(owner)}"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": detail}
    assert appointment.status == AppointmentStatus.REQUESTED
    assert fake_integration_event_bus.events == []


def test_cancel_appointment_route_rejects_terminal_status(
    make_user,
    make_token,
    make_completed_appointment,
    write_uow,
    read_uow,
    fake_integration_event_bus,
):
    owner = make_user()
    write_uow.users.create(owner)
    appointment = make_completed_appointment(user_id=owner.id)
    write_uow.appointments.create(appointment)
    _override_dependencies(write_uow, read_uow, fake_integration_event_bus)

    response = client.patch(
        f"/appointments/{appointment.id}/cancel",
        json={"reason": "Appointment já foi concluído"},
        headers={"Authorization": f"Bearer {make_token(owner)}"},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "appointment_cannot_be_canceled_in_current_status"
    }
    assert appointment.status == AppointmentStatus.COMPLETED
    assert fake_integration_event_bus.events == []
