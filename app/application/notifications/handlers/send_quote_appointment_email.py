from app.application.notifications.handlers.utils.render_quote_appointment_email import (
    render_quote_appointment_client_email,
)
from app.application.notifications.ports.email_service import EmailService
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.domain.studio.appointments.events.notify_of_appointment_quoted import NotifyOfAppointmentQuoted

"""
This handler must fail silently when the client cannot be found.
Email notification failures must not break the booking flow.
"""


class SendQuoteAppointmentEmailHandler:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: NotifyOfAppointmentQuoted, *, uow: ReadUnitOfWork) -> None:
        with uow:
            if isinstance(event.client_email_or_vip_id, str):
                client_email = event.client_email_or_vip_id
            else:
                vip_client = uow.vip_clients.find_by_id(event.client_email_or_vip_id)
                if vip_client is None:
                    return

                client_email = vip_client.email

            html = render_quote_appointment_client_email(
                price=event.price, appointment_type=event.appointment_type
            )

        await self.email_service.send_email(
            to=client_email,
            html_content=html,
            subject="Seu orçamento está pronto!",
        )
