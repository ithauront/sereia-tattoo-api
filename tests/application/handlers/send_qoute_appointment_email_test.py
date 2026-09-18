from decimal import Decimal

from app.application.notifications.handlers.send_quote_appointment_email import (
    SendQuoteAppointmentEmailHandler,
)
from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.appointments.events.notify_of_appointment_quoted import NotifyOfAppointmentQuoted
from tests.fakes.fake_email_service import FakeEmailService


async def test_quote_appointment_sends_email(make_user, read_uow, write_uow):
    user = make_user(email="jhon@doe.com")
    write_uow.users.create(user)

    event = NotifyOfAppointmentQuoted(
        appointment_type=AppointmentType.TATTOO,
        price=Decimal("700"),
        client_email_or_vip_id="jane@doe.com",
    )

    email_service = FakeEmailService()

    handler = SendQuoteAppointmentEmailHandler(email_service=email_service)

    await handler.handle(event, uow=read_uow)

    assert len(email_service.sent_emails) == 1

    assert email_service.sent is True
    assert email_service.last_payload is not None

    assert email_service.last_payload["to"] == "jane@doe.com"
    assert email_service.last_payload["subject"] == "Seu orçamento está pronto!"
    assert "Seu orçamento está pronto!" in email_service.last_payload["html"]
    assert "primeira sessão" not in email_service.last_payload["html"]


async def test_project_quote_email_mentions_first_session_and_total(read_uow):
    event = NotifyOfAppointmentQuoted(
        appointment_type=AppointmentType.TATTOO,
        price=Decimal("700"),
        client_email_or_vip_id="jane@doe.com",
        total_sessions=3,
        current_session=1,
    )
    email_service = FakeEmailService()
    handler = SendQuoteAppointmentEmailHandler(email_service=email_service)

    await handler.handle(event, uow=read_uow)

    assert email_service.last_payload is not None
    assert "primeira sessão" in email_service.last_payload["html"]
    assert "3 sessões" in email_service.last_payload["html"]


async def test_later_project_quote_email_mentions_current_session(read_uow):
    event = NotifyOfAppointmentQuoted(
        appointment_type=AppointmentType.TATTOO,
        price=Decimal("700"),
        client_email_or_vip_id="jane@doe.com",
        total_sessions=3,
        current_session=2,
    )
    email_service = FakeEmailService()
    handler = SendQuoteAppointmentEmailHandler(email_service=email_service)

    await handler.handle(event, uow=read_uow)

    assert email_service.last_payload is not None
    assert "sessão 2 de 3" in email_service.last_payload["html"]
    assert "primeira sessão" not in email_service.last_payload["html"]
