from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.application.notifications.handlers.reschedule_appointment_notificate import (
    SendRescheduleAppointmentEmailHandler,
)
from app.application.notifications.handlers.utils.render_reschedule_appointment_client_email import (
    render_rescheduled_appointment_client_email,
)
from app.application.notifications.handlers.utils.render_rescheduled_appointment_user_email import (
    render_rescheduled_appointment_artist_email,
)
from app.core.exceptions.services import EmailSentFailedError, EmailServiceUnavailableError
from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.appointments.events.notify_appointment_reschedule import (
    NotifyOfAppointmentReschedule,
)
from tests.fakes.fake_email_service import FakeEmailService


def make_event(user_id, recipient, *, retained=False, confirmed=True, kind=AppointmentType.TATTOO):
    return NotifyOfAppointmentReschedule(
        appointment_id=uuid4(),
        user_id=user_id,
        client_email_or_vip_id=recipient,
        start_at=datetime(2035, 1, 10, 14, tzinfo=timezone.utc),
        end_at=datetime(2035, 1, 10, 16, tzinfo=timezone.utc),
        appointment_type=kind,
        was_deposit_retained=retained,
        has_confirmed_deposit=confirmed,
    )


@pytest.mark.parametrize("vip", [False, True])
@pytest.mark.parametrize("kind", list(AppointmentType))
@pytest.mark.parametrize(
    ("retained", "confirmed", "label"),
    [
        (True, False, "CAUÇÃO RETIDA"),
        (False, True, "CAUÇÃO MANTIDA"),
        (False, False, "SEM CAUÇÃO CONFIRMADA"),
    ],
)
async def test_handler_sends_correct_details_and_deposit_state(
    make_user,
    make_vip_client,
    write_uow,
    read_uow,
    vip,
    kind,
    retained,
    confirmed,
    label,
):
    user = make_user(email="artist@example.com")
    write_uow.users.create(user)
    recipient = "client@example.com"
    if vip:
        client = make_vip_client(email=recipient)
        write_uow.vip_clients.create(client)
        recipient = client.id
    event = make_event(user.id, recipient, retained=retained, confirmed=confirmed, kind=kind)
    service = FakeEmailService()
    await SendRescheduleAppointmentEmailHandler(service).handle(event, uow=read_uow)
    assert len(service.sent_emails) == 2
    emails = {email["to"]: email for email in service.sent_emails}
    artist = emails["artist@example.com"]
    client = emails["client@example.com"]
    assert artist["subject"] == "Agendamento foi remarcado"
    assert client["subject"] == "Seu agendamento foi remarcado"
    assert str(event.appointment_id) in artist["html"]
    assert "client@example.com" in artist["html"]
    assert label in artist["html"]
    for email in emails.values():
        assert "10/01/2035" in email["html"]
        assert "14:00 às 16:00 (UTC)" in email["html"]
        assert ("Piercing" if kind == AppointmentType.PIERCING else "Tattoo") in email["html"]
    if retained:
        assert "nova caução" in client["html"]
        assert "aguardando uma nova caução" in artist["html"]
        assert "permanece válida" not in client["html"]
    elif confirmed:
        assert "permanece válida" in client["html"]
        assert "nova caução" not in client["html"]
    else:
        assert "ainda não há caução confirmada" in client["html"]
        assert "permanece válida" not in artist["html"]
        assert "permanece válida" not in client["html"]


@pytest.mark.parametrize("missing", ["user", "vip"])
async def test_missing_recipient_skips_notification(make_user, write_uow, read_uow, missing):
    user = make_user()
    if missing != "user":
        write_uow.users.create(user)
    service = FakeEmailService()
    event = make_event(user.id, uuid4() if missing == "vip" else "client@example.com")
    await SendRescheduleAppointmentEmailHandler(service).handle(event, uow=read_uow)
    assert service.sent_emails == []


@pytest.mark.parametrize(
    ("failure", "error"),
    [
        ("email_service_unavailable", EmailServiceUnavailableError),
        ("email_send_failed", EmailSentFailedError),
    ],
)
async def test_provider_failure_propagates(make_user, write_uow, read_uow, failure, error):
    user = make_user()
    write_uow.users.create(user)
    service = FakeEmailService(fail_with=failure)
    with pytest.raises(error):
        await SendRescheduleAppointmentEmailHandler(service).handle(
            make_event(user.id, "client@example.com"),
            uow=read_uow,
        )


def test_render_escapes_client_email_and_displays_utc_and_end_date():
    start = datetime(2035, 1, 10, 20, tzinfo=timezone(timedelta(hours=-3)))
    end = start + timedelta(hours=2)
    common = dict(
        start_at=start,
        end_at=end,
        appointment_type=AppointmentType.TATTOO,
        was_deposit_retained=False,
        has_confirmed_deposit=True,
    )
    artist = render_rescheduled_appointment_artist_email(
        appointment_id=uuid4(),
        client_email="<b>client</b>&example.com",
        **common,
    )
    assert "<b>client</b>" not in artist
    assert "&lt;b&gt;client&lt;/b&gt;&amp;example.com" in artist
    for html in (artist, render_rescheduled_appointment_client_email(**common)):
        assert "10/01/2035" in html
        assert "23:00 às 11/01/2035 01:00 (UTC)" in html


@pytest.mark.parametrize("failed_recipient", ["artist@example.com", "client@example.com"])
async def test_one_delivery_can_succeed_when_the_other_fails(
    make_user,
    write_uow,
    read_uow,
    failed_recipient,
):
    user = make_user(email="artist@example.com")
    write_uow.users.create(user)

    class PartialFailureService(FakeEmailService):
        async def send_email(self, to, subject, html_content):
            if to == failed_recipient:
                raise EmailSentFailedError()
            await super().send_email(to, subject, html_content)

    service = PartialFailureService()
    with pytest.raises(EmailSentFailedError):
        await SendRescheduleAppointmentEmailHandler(service).handle(
            make_event(user.id, "client@example.com"),
            uow=read_uow,
        )
    assert len(service.sent_emails) == 1
    assert service.sent_emails[0]["to"] != failed_recipient
