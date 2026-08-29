from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.events import get_integration_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work
from app.core.types.appointment_enums import AppointmentStatus
from app.main import app

client = TestClient(app)


def test_quote_appointment_with_admin_route_success(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus, make_appointment_base
):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    owner = make_user()
    write_uow.users.create(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    payload = {"price": "700.50"}

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert response.content == b""

    found = read_uow.appointments.find_by_id(appointment_id=appointment.id)
    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)
    assert found.price == Decimal("700.50")
    assert found.status == AppointmentStatus.QUOTED

    assert len(logs) == 1
    assert logs[0].actor_id == admin.id
    assert logs[0].action == "quote appointment"
    assert len(fake_integration_event_bus.events) == 1

    app.dependency_overrides = {}


def test_quote_appointment_accepts_decimal_comma(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus, make_appointment_base
):
    admin = make_user(is_admin=True)
    write_uow.users.create(admin)
    token = make_token(admin)

    owner = make_user()
    write_uow.users.create(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    payload = {"price": "700,50"}

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert response.content == b""

    found = read_uow.appointments.find_by_id(appointment_id=appointment.id)
    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)
    assert found.price == Decimal("700.50")
    assert found.status == AppointmentStatus.QUOTED

    assert len(logs) == 1
    assert logs[0].actor_id == admin.id
    assert logs[0].action == "quote appointment"
    assert len(fake_integration_event_bus.events) == 1

    app.dependency_overrides = {}


def test_quote_appointment_with_owner_route_success(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus, make_appointment_base
):

    owner = make_user()
    write_uow.users.create(owner)
    token = make_token(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    payload = {"price": "700"}

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204
    assert response.content == b""

    found = read_uow.appointments.find_by_id(appointment_id=appointment.id)
    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)
    assert found.price == Decimal("700")
    assert found.status == AppointmentStatus.QUOTED

    assert len(logs) == 1
    assert logs[0].actor_id == owner.id
    assert logs[0].action == "quote appointment"
    assert len(fake_integration_event_bus.events) == 1

    app.dependency_overrides = {}


def test_quote_appointment_not_found(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus
):
    user = make_user()
    write_uow.users.create(user)
    token = make_token(user)

    # we do not persist appointment for this test

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{uuid4()}/quote",
        json={"price": "700"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "appointment_not_found"

    app.dependency_overrides = {}


def test_quote_appointment_from_another_user_is_forbidden(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus, make_appointment_base
):
    owner = make_user()
    write_uow.users.create(owner)

    another_user = make_user()
    write_uow.users.create(another_user)
    token = make_token(another_user)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json={"price": "700"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "unauthorized_user"

    app.dependency_overrides = {}


def test_quote_appointment_twice_returns_conflict(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus, make_appointment_base
):
    owner = make_user()
    write_uow.users.create(owner)
    token = make_token(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    first_response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json={"price": "700"},
        headers={"Authorization": f"Bearer {token}"},
    )
    second_response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json={"price": "800"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first_response.status_code == 204
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "appointment_cannot_be_quoted_in_current_status"

    app.dependency_overrides = {}


@pytest.mark.parametrize("price", ["0", "-0.01"])
def test_quote_appointment_with_non_positive_price_returns_unprocessable_content(
    price,
    make_user,
    make_token,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_appointment_base,
):
    owner = make_user()
    write_uow.users.create(owner)
    token = make_token(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json={"price": price},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert appointment.status == AppointmentStatus.REQUESTED
    assert fake_integration_event_bus.events == []

    app.dependency_overrides = {}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"price": "not-a-decimal"},
        {"price": "4.700.50"},
        {"price": "4,700,50"},
        {"price": "700.501"},
    ],
)
def test_quote_appointment_with_invalid_payload_returns_unprocessable_content(
    payload,
    make_user,
    make_token,
    write_uow,
    read_uow,
    fake_integration_event_bus,
    make_appointment_base,
):
    owner = make_user()
    write_uow.users.create(owner)
    token = make_token(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert appointment.status == AppointmentStatus.REQUESTED
    assert fake_integration_event_bus.events == []

    app.dependency_overrides = {}


def test_quote_appointment_with_invalid_id_returns_unprocessable_content(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus
):
    user = make_user()
    write_uow.users.create(user)
    token = make_token(user)

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        "/appointments/not-an-uuid/quote",
        json={"price": "700"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


def test_quote_appointment_with_inactive_user_is_forbidden(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus, make_appointment_base
):
    owner = make_user(is_active=False)
    write_uow.users.create(owner)
    token = make_token(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json={"price": "700"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "inactive_user"

    app.dependency_overrides = {}


def test_quote_appointment_with_nonexistent_user_returns_unauthorized(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus, make_appointment_base
):
    owner = make_user()
    token = make_token(owner)

    appointment = make_appointment_base(user_id=owner.id)
    write_uow.appointments.create(appointment)

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json={"price": "700"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_credentials"

    app.dependency_overrides = {}


def test_quote_appointment_with_corrupted_client_info_returns_internal_server_error(
    make_user, make_token, write_uow, read_uow, fake_integration_event_bus, make_appointment_base
):
    owner = make_user()
    write_uow.users.create(owner)
    token = make_token(owner)

    appointment = make_appointment_base(user_id=owner.id)
    appointment.client_info.email = None
    appointment.client_info.vip_client_id = None
    write_uow.appointments.create(appointment)

    app.dependency_overrides[get_integration_event_bus] = lambda: fake_integration_event_bus
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/quote",
        json={"price": "700"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "appointment_is_broken"

    app.dependency_overrides = {}
