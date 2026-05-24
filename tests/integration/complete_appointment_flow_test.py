from decimal import Decimal
from fastapi.testclient import TestClient

from app.core.types.appointment_enums import AppointmentStatus
from app.main import app

from app.api.dependencies.events import get_event_bus
from app.api.dependencies.read_unit_of_work import get_read_unit_of_work
from app.api.dependencies.write_unit_of_work import get_write_unit_of_work

from app.application.event_bus.setup import setup_event_bus

from app.core.types.payment_enums import PaymentMethodType
from app.core.types.client_credit_source_type import ClientCreditSourceType

client = TestClient(app)


def test_complete_appointment_generates_referral_credits(
    write_uow,
    read_uow,
    make_user,
    make_token,
    jwt_service_instance,
    make_vip_client,
    make_scheduled_appointment,
    make_payment,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_scheduled_appointment(
        referral_code=vip_client.client_code, price=Decimal("700")
    )
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700"),
        payment_method=PaymentMethodType.PIX,
    )
    write_uow.payments.create(payment)

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=None,
        token_service=jwt_service_instance,
        write_uow_factory=lambda: write_uow,
    )
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 204

    updated_appointment = write_uow.appointments.find_by_id(appointment.id)

    assert updated_appointment.status == AppointmentStatus.COMPLETED

    entries = write_uow.client_credit_entries.find_many_by_source_id(
        source_id=appointment.id
    )

    assert len(entries) == 1

    entry = entries[0]

    assert entry.vip_client_id == vip_client.id
    assert entry.source_type == ClientCreditSourceType.INDICATION

    assert entry.quantity == 70

    app.dependency_overrides = {}


def test_complete_appointment_failure_does_not_generate_credits(
    write_uow,
    read_uow,
    make_user,
    make_token,
    jwt_service_instance,
    make_vip_client,
    make_scheduled_appointment,
    make_payment,
):
    admin = make_user(is_admin=True, email="admin@admin.com")
    write_uow.users.create(admin)

    token = make_token(admin)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_scheduled_appointment(
        referral_code=vip_client.client_code, price=Decimal("700")
    )
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("500"),
        payment_method=PaymentMethodType.PIX,
    )
    write_uow.payments.create(payment)

    app.dependency_overrides[get_event_bus] = lambda: setup_event_bus(
        email_service=None,
        token_service=jwt_service_instance,
        write_uow_factory=lambda: write_uow,
    )
    app.dependency_overrides[get_write_unit_of_work] = lambda: write_uow
    app.dependency_overrides[get_read_unit_of_work] = lambda: read_uow

    response = client.patch(
        f"/appointments/{appointment.id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409

    not_updated_appointment = write_uow.appointments.find_by_id(appointment.id)

    assert not_updated_appointment.status == AppointmentStatus.SCHEDULED

    entries = write_uow.client_credit_entries.find_many_by_source_id(
        source_id=appointment.id
    )

    assert len(entries) == 0

    app.dependency_overrides = {}
