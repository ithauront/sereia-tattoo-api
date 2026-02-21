from app.application.notifications.ports.email_service import EmailService
from app.infrastructure.email.brevo_email_service import BrevoEmailService


def get_email_service() -> EmailService:
    return BrevoEmailService()
