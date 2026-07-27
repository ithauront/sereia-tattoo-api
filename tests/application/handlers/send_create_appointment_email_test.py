from datetime import datetime, timedelta

from app.application.notifications.handlers.send_create_appointment_email import (
    SendCreateAppointmentEmailHandler,
)
from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.appointments.events.create_appointment_request import (
    CreateAppointmentEmailRequested,
)
from tests.fakes.fake_email_service import FakeEmailService


async def test_send_create_appointment_sends_email(make_user, read_uow, write_uow):
    start_at = datetime.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=2)
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

    event = CreateAppointmentEmailRequested(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        client_email_or_vip_code="jane@doe.com",
    )

    email_service = FakeEmailService()

    handler = SendCreateAppointmentEmailHandler(email_service=email_service)

    await handler.handle(event, read_uow)

    assert len(email_service.sent_emails) == 2

    user_email = next(email for email in email_service.sent_emails if email["to"] == "jhon@doe.com")

    client_email = next(email for email in email_service.sent_emails if email["to"] == "jane@doe.com")

    assert user_email["subject"] == "Novo agendamento solicitado"
    assert "Quanto mais rápido o atendimento, maior a chance de converter" in user_email["html"]
    assert client_email["subject"] == "Recebemos sua solicitação de agendamento"
    assert "Nossa equipe vai analisar sua solicitação e entrar em contato" in client_email["html"]


async def test_send_create_appointment_sends_email_with_vip_code(
    make_user, read_uow, write_uow, make_vip_client
):
    start_at = datetime.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=2)
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)
    vip_client = make_vip_client(email="jane@doe.com")
    write_uow.vip_clients.create(vip_client)

    event = CreateAppointmentEmailRequested(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        client_email_or_vip_code=vip_client.client_code,
    )

    email_service = FakeEmailService()

    handler = SendCreateAppointmentEmailHandler(email_service=email_service)

    await handler.handle(event, read_uow)

    assert len(email_service.sent_emails) == 2

    user_email = next(email for email in email_service.sent_emails if email["to"] == "jhon@doe.com")

    client_email = next(email for email in email_service.sent_emails if email["to"] == "jane@doe.com")

    assert user_email["subject"] == "Novo agendamento solicitado"
    assert client_email["subject"] == "Recebemos sua solicitação de agendamento"


async def test_send_create_appointment_vip_client_not_found_does_not_sends_email(
    make_user, read_uow, write_uow, make_vip_client
):
    start_at = datetime.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=2)
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)
    vip_client = make_vip_client(email="jane@doe.com")
    # we do not persist vip client for this test

    event = CreateAppointmentEmailRequested(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        client_email_or_vip_code=vip_client.client_code,
    )

    email_service = FakeEmailService()

    handler = SendCreateAppointmentEmailHandler(email_service=email_service)

    await handler.handle(event, read_uow)

    assert len(email_service.sent_emails) == 0

    assert email_service.sent is False


async def test_send_create_appointment_user_not_found_does_not_sends_email(
    make_user, read_uow, write_uow, make_vip_client
):
    start_at = datetime.now() + timedelta(days=1)
    end_at = start_at + timedelta(hours=2)
    user = make_user(email="jhon@doe.com")
    # we do not persist user for this test
    vip_client = make_vip_client(email="jane@doe.com")
    write_uow.vip_clients.create(vip_client)

    event = CreateAppointmentEmailRequested(
        appointment_type=AppointmentType.TATTOO,
        user_id=user.id,
        start_at=start_at,
        end_at=end_at,
        client_email_or_vip_code=vip_client.client_code,
    )

    email_service = FakeEmailService()

    handler = SendCreateAppointmentEmailHandler(email_service=email_service)

    await handler.handle(event, read_uow)

    assert len(email_service.sent_emails) == 0

    assert email_service.sent is False
