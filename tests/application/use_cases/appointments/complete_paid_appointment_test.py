from decimal import Decimal
from app.application.studio.use_cases.appointments_use_cases.complete_paid_appointment_use_case import CompletePaidAppointmentUseCase, CompletePaidAppointmentInput
from tests.fakes.fake_event_bus import FakeEventBus
from app.core.types.appointment_enums import (
    AppointmentStatus,
)
import pytest
from app.domain.studio.appointments.events.appointment_completed import AppointmentCompleted
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.core.exceptions.appointments import AppointmentWasNotFullyPaidError, AppointmentMustBeScheduledError, AppointmentNotFoundError
from pydantic import ValidationError

@pytest.mark.asyncio
async def test_complete_paid_appointment_successful(make_user, make_scheduled_appointment, make_payment, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)
    
    appointment = make_scheduled_appointment(price=Decimal('700'))
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal('700'))
    write_uow.payments.create(payment)

    event_bus= FakeEventBus()

    use_case = CompletePaidAppointmentUseCase(uow=write_uow, event_bus=event_bus)
    dto = CompletePaidAppointmentInput(actor_id=user.id, appointment_id=appointment.id)

    await use_case.execute(dto)

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)

    assert appointment_in_repo.status == AppointmentStatus.COMPLETED

    #Appointment without referral_code should not create event
    assert len(event_bus.events) == 0

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert len(logs) == 1



@pytest.mark.asyncio
async def test_complete_paid_appointment_with_referral_successful(make_user, make_vip_client, make_scheduled_appointment, make_payment, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)
    
    
    appointment = make_scheduled_appointment(price=Decimal('700'), referral_code=vip_client.client_code)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal('700'))
    write_uow.payments.create(payment)

    event_bus= FakeEventBus()

    use_case = CompletePaidAppointmentUseCase(uow=write_uow, event_bus=event_bus)
    dto = CompletePaidAppointmentInput(actor_id=user.id, appointment_id=appointment.id)

    await use_case.execute(dto)

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)

    assert appointment_in_repo.status == AppointmentStatus.COMPLETED

    assert len(event_bus.events) == 1
    event = event_bus.events[0]

    assert isinstance(event, AppointmentCompleted)
    assert event.appointment_id == appointment.id
    assert event.client_info.vip_client_id is None
    assert event.client_info.email == appointment.client_info.email
    assert event.client_info.name == appointment.client_info.name
    assert event.client_info.phone == appointment.client_info.phone
    assert event.referral_code == vip_client.client_code

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert len(logs) == 1

@pytest.mark.asyncio
async def test_complete_paid_appointment_with_self_referral_successful(make_user, make_vip_client, make_scheduled_appointment, make_payment, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)

    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)
    
    vip_client_info = ClientInfo(vip_client_id=vip_client.id)
    
    appointment = make_scheduled_appointment(price=Decimal('700'), referral_code=vip_client.client_code, client_info =vip_client_info)
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal('700'))
    write_uow.payments.create(payment)

    event_bus= FakeEventBus()

    use_case = CompletePaidAppointmentUseCase(uow=write_uow, event_bus=event_bus)
    dto = CompletePaidAppointmentInput(actor_id=user.id, appointment_id=appointment.id)

    await use_case.execute(dto)

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)

    assert appointment_in_repo.status == AppointmentStatus.COMPLETED

    assert len(event_bus.events) == 1
    event = event_bus.events[0]

    assert isinstance(event, AppointmentCompleted)
    assert event.appointment_id == appointment.id
    assert event.client_info.vip_client_id == vip_client.id
    assert event.client_info.email is None
    assert event.client_info.name is None
    assert event.client_info.phone is None
    assert event.referral_code == vip_client.client_code

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert len(logs) == 1

@pytest.mark.asyncio
async def test_complete_paid_appointment_create_log(make_user, make_scheduled_appointment, make_payment, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)
    
    appointment = make_scheduled_appointment(price=Decimal('700'))
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal('700'))
    write_uow.payments.create(payment)

    event_bus= FakeEventBus()

    use_case = CompletePaidAppointmentUseCase(uow=write_uow, event_bus=event_bus)
    dto = CompletePaidAppointmentInput(actor_id=user.id, appointment_id=appointment.id)

    await use_case.execute(dto)

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert len(logs) == 1
    log = logs[0]
    
    assert log.actor_id == user.id
    assert log.entity_id == appointment.id
    assert log.changes["status"]["from"] == AppointmentStatus.SCHEDULED.value
    assert log.changes["status"]["to"] == AppointmentStatus.COMPLETED.value
    assert log.changes["payment"]["total_paid"] == Decimal("700")

@pytest.mark.asyncio
async def test_appointment_not_fully_paid(make_user, make_scheduled_appointment, make_payment, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)
    
    appointment = make_scheduled_appointment(price=Decimal('700'))
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal('650'))
    write_uow.payments.create(payment)

    event_bus= FakeEventBus()

    use_case = CompletePaidAppointmentUseCase(uow=write_uow, event_bus=event_bus)
    dto = CompletePaidAppointmentInput(actor_id=user.id, appointment_id=appointment.id)

    with pytest.raises(AppointmentWasNotFullyPaidError):
        await use_case.execute(dto)

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)

    assert appointment_in_repo.status == AppointmentStatus.SCHEDULED

    assert len(event_bus.events) == 0

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert logs == []


@pytest.mark.asyncio
async def test_appointment_was_not_in_correct_status(make_user, make_quoted_appointment, make_payment, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)
    
    #make appointment in wrong status
    appointment = make_quoted_appointment(price=Decimal('700'))
    write_uow.appointments.create(appointment)

    payment = make_payment(appointment_id=appointment.id, amount=Decimal('700'))
    write_uow.payments.create(payment)

    event_bus= FakeEventBus()

    use_case = CompletePaidAppointmentUseCase(uow=write_uow, event_bus=event_bus)
    dto = CompletePaidAppointmentInput(actor_id=user.id, appointment_id=appointment.id)

    with pytest.raises(AppointmentMustBeScheduledError):
        await use_case.execute(dto)

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)

    assert appointment_in_repo.status == AppointmentStatus.QUOTED

    assert len(event_bus.events) == 0

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert logs == []


@pytest.mark.asyncio
async def test_appointment_not_persisted_paid(make_user, make_scheduled_appointment, make_payment, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)
    
    appointment = make_scheduled_appointment(price=Decimal('700'))
    # we do not persist appointment for this test

    payment = make_payment(appointment_id=appointment.id, amount=Decimal('700'))
    write_uow.payments.create(payment)

    event_bus= FakeEventBus()

    use_case = CompletePaidAppointmentUseCase(uow=write_uow, event_bus=event_bus)
    dto = CompletePaidAppointmentInput(actor_id=user.id, appointment_id=appointment.id)

    with pytest.raises(AppointmentNotFoundError):
        await use_case.execute(dto)

    appointment_in_repo = read_uow.appointments.find_by_id(appointment_id=appointment.id)

    assert appointment_in_repo.status == AppointmentStatus.SCHEDULED

    assert len(event_bus.events) == 0

    logs = read_uow.audit_logs.find_many_by_entity_id(appointment.id)

    assert logs == []

def test_complete_paid_appointment_input_requires_valid_uuids():
    with pytest.raises(ValidationError):
        CompletePaidAppointmentInput(
            actor_id="not_a_uuid",
            appointment_id="not_a_uuid",
        )