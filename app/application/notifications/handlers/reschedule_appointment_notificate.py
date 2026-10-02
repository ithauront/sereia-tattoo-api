import asyncio

from app.application.notifications.handlers.utils.render_reschedule_appointment_client_email import (
    render_rescheduled_appointment_client_email,
)
from app.application.notifications.handlers.utils.render_rescheduled_appointment_user_email import (
    render_rescheduled_appointment_artist_email,
)
from app.application.notifications.ports.email_service import EmailService
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.domain.studio.appointments.events.notify_appointment_reschedule import (
    NotifyOfAppointmentReschedule,
)

"""
Silent returns are intentional.

This handler processes a notification event asynchronously.
If the target user or VIP client no longer exists by the time
the event is handled, there is no meaningful recovery action.
The appointment has already been created, so the notification
is simply skipped instead of failing the event processing.

Infrastructure failures (email provider unavailable, etc.)
must still propagate, allowing retries according to the
configured event processing strategy.
"""


class SendRescheduleAppointmentEmailHandler:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: NotifyOfAppointmentReschedule, *, uow: ReadUnitOfWork) -> None:

        if isinstance(event.client_email_or_vip_id, str):
            client_email = event.client_email_or_vip_id
        else:
            vip_client = uow.vip_clients.find_by_id(event.client_email_or_vip_id)
            if vip_client is None:
                return
            client_email = vip_client.email

        user = uow.users.find_by_id(event.user_id)
        if user is None:
            return
        user_email = user.email

        appointment_type = event.appointment_type

        html_user = render_rescheduled_appointment_artist_email(
            appointment_id=event.appointment_id,
            start_at=event.start_at,
            end_at=event.end_at,
            appointment_type=appointment_type,
            was_deposit_retained=event.was_deposit_retained,
            has_confirmed_deposit=event.has_confirmed_deposit,
            client_email=client_email,
        )

        html_client = render_rescheduled_appointment_client_email(
            start_at=event.start_at,
            end_at=event.end_at,
            appointment_type=appointment_type,
            was_deposit_retained=event.was_deposit_retained,
            has_confirmed_deposit=event.has_confirmed_deposit,
        )

        await asyncio.gather(
            self.email_service.send_email(
                to=user_email,
                subject="Agendamento foi remarcado",
                html_content=html_user,
            ),
            self.email_service.send_email(
                to=client_email,
                subject="Seu agendamento foi remarcado",
                html_content=html_client,
            ),
        )
