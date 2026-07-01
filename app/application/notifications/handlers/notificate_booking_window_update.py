from app.application.notifications.handlers.utils.render_booking_window_email import (
    render_booking_window_email,
)
from app.application.notifications.ports.email_service import EmailService
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork
from app.domain.studio.appointments.events.booking_window_updated import BookingWindowUpdated

"""
Silent returns in this handler prevent from breaking the booking window flow.
If a error happens here the only consequence is the email will not be sent.
"""


# TODO: esse handler vai ser chamado em duas situações
# 1 no usecase de atualizar booking manualmente a gente vai publicar o evento no integration bus e passar o uow
# 2 no script de atualizar booking automaticamente a gente vai publicar o evento no integration bus e passar o uow
class NotificateBookingWindowUpdateHandler:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: BookingWindowUpdated, *, uow: ReadUnitOfWork) -> None:
        with uow:
            user = uow.users.find_by_id(event.user_id)
            if user is None:
                return

            user_email = user.email

            html = render_booking_window_email(new_booking_window=event.new_booking_window)

        await self.email_service.send_email(
            to=user_email, html_content=html, subject="Um novo periodo de disponibilidade foi aberto."
        )
