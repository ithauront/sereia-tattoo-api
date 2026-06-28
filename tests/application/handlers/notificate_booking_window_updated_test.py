from datetime import datetime, timezone

from app.application.notifications.handlers.notificate_booking_window_update import (
    NotificateBookingWindowUpdateHandler,
)
from app.domain.studio.appointments.events.booking_window_updated import BookingWindowUpdated
from tests.fakes.fake_email_service import FakeEmailService


async def test_notificate_booking_window_handler_sends_email(make_user, write_uow, read_uow):
    user = make_user()
    write_uow.users.create(user)

    updated_booking_window_date = datetime(2030, 1, 1, tzinfo=timezone.utc).date()

    event = BookingWindowUpdated(user_id=user.id, new_booking_window=updated_booking_window_date)

    email_service = FakeEmailService()

    handler = NotificateBookingWindowUpdateHandler(email_service=email_service)

    await handler.handle(event=event, uow=read_uow)

    assert email_service.sent is True
    assert email_service.last_payload is not None

    assert email_service.last_payload["to"] == "jhon@doe.com"
    assert email_service.last_payload["subject"] == "Um novo periodo de disponibilidade foi aberto."
    assert (
        "Novas datas estão disponiveis para agendamento com você!" in email_service.last_payload["html"]
    )


async def test_notificate_booking_window_handler_user_not_found(make_user, write_uow, read_uow):
    user = make_user()
    # we do not persist user for this test

    updated_booking_window_date = datetime(2030, 1, 1, tzinfo=timezone.utc).date()

    event = BookingWindowUpdated(user_id=user.id, new_booking_window=updated_booking_window_date)

    email_service = FakeEmailService()

    handler = NotificateBookingWindowUpdateHandler(email_service=email_service)

    await handler.handle(event=event, uow=read_uow)

    assert email_service.sent is False
