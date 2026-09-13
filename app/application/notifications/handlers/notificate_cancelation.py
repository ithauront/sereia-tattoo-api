import asyncio

from app.application.notifications.handlers.utils.render_appointment_cancellation_client_email import (
    render_appointment_cancellation_client_email,
)
from app.application.notifications.handlers.utils.render_appointment_cancellation_user_email import (
    render_appointment_cancellation_user_email,
)
from app.application.notifications.ports.email_service import EmailService
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.domain.studio.appointments.events.cancel_appointment import CancelAppointmentEmailRequested

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


class NotificateAppointmentCanceledEmailHandler:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: CancelAppointmentEmailRequested, *, uow: ReadUnitOfWork) -> None:

        if isinstance(event.client_email_or_vip_id, str):
            client_email = event.client_email_or_vip_id
        else:
            vip_client = uow.vip_clients.find_by_id(event.client_email_or_vip_id)
            if vip_client is None:
                return
            else:
                client_email = vip_client.email

        user = uow.users.find_by_id(event.user_id)
        if user is None:
            return
        user_email = user.email

        appointment_type = event.appointment_type.value

        html_user = render_appointment_cancellation_user_email(
            start_at=event.start_at,
            end_at=event.end_at,
            appointment_type=appointment_type,
            has_confirmed_deposit=event.has_confirmed_deposit,
            is_eligible_for_deposit_refund=event.is_eligible_for_deposit_refund,
        )

        html_client = render_appointment_cancellation_client_email(
            start_at=event.start_at,
            end_at=event.end_at,
            appointment_type=appointment_type,
            has_confirmed_deposit=event.has_confirmed_deposit,
            is_eligible_for_deposit_refund=event.is_eligible_for_deposit_refund,
        )

        if not event.has_confirmed_deposit:
            user_subject = "Agendamento cancelado — sem caução confirmada"
        elif event.is_eligible_for_deposit_refund:
            user_subject = "Agendamento cancelado — caução reembolsável"
        else:
            user_subject = "Agendamento cancelado — caução não reembolsável"

        await asyncio.gather(
            self.email_service.send_email(
                to=user_email,
                subject=user_subject,
                html_content=html_user,
            ),
            self.email_service.send_email(
                to=client_email,
                subject="Seu horário agendado foi cancelado",
                html_content=html_client,
            ),
        )
