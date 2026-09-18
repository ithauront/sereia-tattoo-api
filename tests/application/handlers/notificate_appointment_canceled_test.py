from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.application.notifications.handlers.notificate_cancelation import (
    NotificateAppointmentCanceledEmailHandler,
)
from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.appointments.events.cancel_appointment import (
    CancelAppointmentEmailRequested,
)
from tests.fakes.fake_email_service import FakeEmailService


def _event(
    *,
    user_id,
    client_email_or_vip_id,
    is_eligible_for_deposit_refund,
    has_confirmed_deposit=True,
):
    start_at = datetime(2030, 1, 10, 14, tzinfo=timezone.utc)
    return CancelAppointmentEmailRequested(
        start_at=start_at,
        end_at=start_at + timedelta(hours=2),
        appointment_type=AppointmentType.TATTOO,
        user_id=user_id,
        client_email_or_vip_id=client_email_or_vip_id,
        has_confirmed_deposit=has_confirmed_deposit,
        is_eligible_for_deposit_refund=is_eligible_for_deposit_refund,
    )


async def test_cancellation_handler_notifies_user_and_client_without_telling_eligible_client(
    make_user, write_uow, read_uow
):
    user = make_user(email="artist@example.com")
    write_uow.users.create(user)
    email_service = FakeEmailService()
    handler = NotificateAppointmentCanceledEmailHandler(email_service)

    await handler.handle(
        _event(
            user_id=user.id,
            client_email_or_vip_id="client@example.com",
            is_eligible_for_deposit_refund=True,
        ),
        uow=read_uow,
    )

    assert len(email_service.sent_emails) == 2
    artist_email = next(
        email for email in email_service.sent_emails if email["to"] == "artist@example.com"
    )
    client_email = next(
        email for email in email_service.sent_emails if email["to"] == "client@example.com"
    )
    assert artist_email["subject"] == "Agendamento cancelado — caução reembolsável"
    assert "é elegível para reembolso" in artist_email["html"]
    assert client_email["subject"] == "Seu horário agendado foi cancelado"
    assert "não permite o reembolso" not in client_email["html"]


async def test_cancellation_handler_warns_both_recipients_when_refund_is_not_allowed(
    make_user, make_vip_client, write_uow, read_uow
):
    user = make_user(email="artist@example.com")
    vip_client = make_vip_client(email="client@example.com")
    write_uow.users.create(user)
    write_uow.vip_clients.create(vip_client)
    email_service = FakeEmailService()
    handler = NotificateAppointmentCanceledEmailHandler(email_service)

    await handler.handle(
        _event(
            user_id=user.id,
            client_email_or_vip_id=vip_client.id,
            is_eligible_for_deposit_refund=False,
        ),
        uow=read_uow,
    )

    assert len(email_service.sent_emails) == 2
    artist_email = next(
        email for email in email_service.sent_emails if email["to"] == "artist@example.com"
    )
    client_email = next(
        email for email in email_service.sent_emails if email["to"] == "client@example.com"
    )
    assert artist_email["subject"] == "Agendamento cancelado — caução não reembolsável"
    assert "não é elegível para reembolso" in artist_email["html"]
    assert "não permite o reembolso" in client_email["html"]


async def test_cancellation_handler_tells_user_when_there_is_no_confirmed_deposit(
    make_user, write_uow, read_uow
):
    user = make_user(email="artist@example.com")
    write_uow.users.create(user)
    email_service = FakeEmailService()
    handler = NotificateAppointmentCanceledEmailHandler(email_service)

    await handler.handle(
        _event(
            user_id=user.id,
            client_email_or_vip_id="client@example.com",
            has_confirmed_deposit=False,
            is_eligible_for_deposit_refund=False,
        ),
        uow=read_uow,
    )

    artist_email = next(
        email for email in email_service.sent_emails if email["to"] == "artist@example.com"
    )
    client_email = next(
        email for email in email_service.sent_emails if email["to"] == "client@example.com"
    )
    assert artist_email["subject"] == "Agendamento cancelado — sem caução confirmada"
    assert "não havia confirmado o pagamento da caução" in artist_email["html"]
    assert "não permite o reembolso" not in client_email["html"]


async def test_cancellation_handler_skips_notification_when_user_no_longer_exists(read_uow):
    email_service = FakeEmailService()
    handler = NotificateAppointmentCanceledEmailHandler(email_service)

    await handler.handle(
        _event(
            user_id=uuid4(),
            client_email_or_vip_id="client@example.com",
            is_eligible_for_deposit_refund=False,
        ),
        uow=read_uow,
    )

    assert email_service.sent_emails == []


async def test_cancellation_handler_skips_notification_when_vip_client_no_longer_exists(
    make_user, write_uow, read_uow
):
    user = make_user(email="artist@example.com")
    write_uow.users.create(user)
    email_service = FakeEmailService()
    handler = NotificateAppointmentCanceledEmailHandler(email_service)

    await handler.handle(
        _event(
            user_id=user.id,
            client_email_or_vip_id=uuid4(),
            is_eligible_for_deposit_refund=False,
        ),
        uow=read_uow,
    )

    assert email_service.sent_emails == []
