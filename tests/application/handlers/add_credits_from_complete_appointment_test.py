from decimal import Decimal
from uuid import uuid4

from app.application.studio.handlers.add_credits_from_completed_appointment import (
    AddCreditsFromCompletedAppointmentHandler,
)
from app.core.types.audit_actor_type import AuditActorType
from app.core.types.client_credit_source_type import ClientCreditSourceType
from app.core.types.payment_enums import PaymentMethodType
from app.domain.studio.appointments.entities.value_objects.client_info import ClientInfo
from app.domain.studio.appointments.events.appointment_completed import (
    AppointmentCompleted,
)
from app.domain.studio.value_objects.client_code import ClientCode


async def test_should_create_10_percent_credit_for_indication(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700"),
    )
    write_uow.payments.create(payment)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 70

    quantity_of_entries = read_uow.client_credit_entries.count_by_vip_client_id(
        vip_client_id=vip_client.id
    )
    assert quantity_of_entries == 1

    client_credits = read_uow.client_credit_entries.find_many_by_vip_client_id(
        vip_client_id=vip_client.id
    )
    client_credit = client_credits[0]
    assert client_credit.source_id == appointment.id
    assert client_credit.source_type == ClientCreditSourceType.INDICATION
    assert client_credit.reason == "Créditos referentes a indicação."

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    assert len(logs) == 1
    log = logs[0]

    assert log.action == "create credits from appointment done"
    assert log.actor_id is None
    assert log.actor_type == AuditActorType.SYSTEM
    assert log.changes == {
        "balance": {
            "from": 0,
            "to": 70,
        },
        "credit": {
            "source_type": ClientCreditSourceType.INDICATION,
            "quantity": 70,
        },
        "vip_client": {
            "id": vip_client.id,
            "client_code": vip_client.client_code,
        },
        "appointment": {
            "id": appointment.id,
        },
    }
    assert log.reason == "credits from referral in appointment"


async def test_ceil_should_round_for_more(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700.5"))
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700.5"),
    )
    write_uow.payments.create(payment)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 71


async def test_should_create_5_percent_credit_for_self_referral(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700"),
    )
    write_uow.payments.create(payment)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(vip_client_id=vip_client.id),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )

    assert credits_created == 35

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    log = logs[0]

    assert log.action == "create credits from appointment done"
    assert log.actor_id is None
    assert log.actor_type == AuditActorType.SYSTEM
    assert log.changes == {
        "balance": {
            "from": 0,
            "to": 35,
        },
        "credit": {
            "source_type": ClientCreditSourceType.INDICATION,
            "quantity": 35,
        },
        "vip_client": {
            "id": vip_client.id,
            "client_code": vip_client.client_code,
        },
        "appointment": {
            "id": appointment.id,
        },
    }
    assert log.reason == "credits from referral in appointment"


async def test_add_credits_client_has_credits_before(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
    make_client_credit_entry,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700"),
    )
    write_uow.payments.create(payment)

    old_credits_for_client = make_client_credit_entry(
        quantity=50, vip_client_id=vip_client.id
    )
    write_uow.client_credit_entries.create(old_credits_for_client)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    total_credits = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert total_credits == 120

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    log = logs[0]

    assert log.changes == {
        "balance": {
            "from": 50,
            "to": 120,
        },
        "credit": {
            "source_type": ClientCreditSourceType.INDICATION,
            "quantity": 70,
        },
        "vip_client": {
            "id": vip_client.id,
            "client_code": vip_client.client_code,
        },
        "appointment": {
            "id": appointment.id,
        },
    }


async def test_part_of_payment_from_credits(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment_pix = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("500"),
        payment_method=PaymentMethodType.PIX,
    )
    write_uow.payments.create(payment_pix)

    payment_card = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("100"),
        payment_method=PaymentMethodType.CARD,
    )
    write_uow.payments.create(payment_card)

    payment_with_credits = make_payment(
        payment_method=PaymentMethodType.CLIENT_CREDIT,
        appointment_id=appointment.id,
        amount=Decimal("100"),
    )
    write_uow.payments.create(payment_with_credits)

    # 700 total paid but only 600 (pix and card) count for making credit

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 60


async def test_total_payment_from_credits(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment_with_credits = make_payment(
        payment_method=PaymentMethodType.CLIENT_CREDIT,
        appointment_id=appointment.id,
        amount=Decimal("700"),
    )
    write_uow.payments.create(payment_with_credits)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    assert logs == []


async def test_existing_entry_should_silent_return(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
    make_client_credit_entry,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700"),
        payment_method=PaymentMethodType.PIX,
    )
    write_uow.payments.create(payment)

    existing_client_credit_entry = make_client_credit_entry(
        source_id=appointment.id,
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.INDICATION,
        quantity=10,
    )
    write_uow.client_credit_entries.create(existing_client_credit_entry)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 10  # only the existing entry

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    assert logs == []


async def test_existing_credits_from_other_sources_should_not_prevent_addition(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
    make_client_credit_entry,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700"),
        payment_method=PaymentMethodType.PIX,
    )
    write_uow.payments.create(payment)

    existing_client_credit_entry = make_client_credit_entry(
        source_id=uuid4(),
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.INDICATION,
        quantity=10,
    )
    write_uow.client_credit_entries.create(existing_client_credit_entry)

    existing_client_credit_entry = make_client_credit_entry(
        source_id=appointment.id,
        vip_client_id=vip_client.id,
        source_type=ClientCreditSourceType.ADDED_BY_ADMIN,
        quantity=10,
    )
    write_uow.client_credit_entries.create(existing_client_credit_entry)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 90

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    log = logs[0]

    assert log.changes == {
        "balance": {
            "from": 20,
            "to": 90,
        },
        "credit": {
            "source_type": ClientCreditSourceType.INDICATION,
            "quantity": 70,
        },
        "vip_client": {
            "id": vip_client.id,
            "client_code": vip_client.client_code,
        },
        "appointment": {
            "id": appointment.id,
        },
    }


async def test_non_existing_referral_code_should_silent_return(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700"),
        payment_method=PaymentMethodType.PIX,
    )
    write_uow.payments.create(payment)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=ClientCode(value="WRONG-CODE"),
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    assert logs == []


async def test_add_credits_from_correct_appointment(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment_a = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment_a)

    appointment_b = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment_b)

    payment_correct_1 = make_payment(
        appointment_id=appointment_b.id,
        amount=Decimal("500"),
    )
    write_uow.payments.create(payment_correct_1)
    payment_correct_2 = make_payment(
        appointment_id=appointment_b.id,
        amount=Decimal("200"),
    )
    write_uow.payments.create(payment_correct_2)

    payment_wrong = make_payment(
        appointment_id=appointment_a.id,
        amount=Decimal("700"),
    )
    write_uow.payments.create(payment_wrong)

    event = AppointmentCompleted(
        appointment_id=appointment_b.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 70

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    log = logs[0]

    assert log.changes == {
        "balance": {
            "from": 0,
            "to": 70,
        },
        "credit": {
            "source_type": ClientCreditSourceType.INDICATION,
            "quantity": 70,
        },
        "vip_client": {
            "id": vip_client.id,
            "client_code": vip_client.client_code,
        },
        "appointment": {
            "id": appointment_b.id,
        },
    }


async def test_handler_is_idempotent(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
    make_payment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    payment = make_payment(
        appointment_id=appointment.id,
        amount=Decimal("700"),
    )
    write_uow.payments.create(payment)

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=vip_client.client_code,
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)
    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 70

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    assert len(logs) == 1


async def test_total_less_equal_to_zero_should_silent_return(
    write_uow,
    read_uow,
    make_vip_client,
    make_completed_appointment,
):
    vip_client = make_vip_client()
    write_uow.vip_clients.create(vip_client)

    appointment = make_completed_appointment(price=Decimal("700"))
    write_uow.appointments.create(appointment)

    # we do not make payment in this test

    event = AppointmentCompleted(
        appointment_id=appointment.id,
        referral_code=ClientCode(value="WRONG-CODE"),
        client_info=ClientInfo(
            name="jane",
            email="jane@doe.com",
            phone="011988888888",
        ),
    )

    handler = AddCreditsFromCompletedAppointmentHandler()

    await handler.handle(event=event, context=write_uow)

    credits_created = read_uow.client_credit_entries.get_balance(
        vip_client_id=vip_client.id
    )
    assert credits_created == 0

    logs = read_uow.audit_logs.find_many_by_entity_name(
        entity_name="client_credit_entry"
    )
    assert logs == []
