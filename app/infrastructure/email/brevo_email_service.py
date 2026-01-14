import logging
import httpx
from app.core.config import settings
from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
)
from app.domain.notifications.ports.email_service import EmailService

logger = logging.getLogger(__name__)


class BrevoEmailService(EmailService):

    async def send_email(self, to: str, subject: str, html_content: str) -> None:
        url = "https://api.brevo.com/v3/smtp/email"

        payload = {
            "sender": {
                "email": settings.BREVO_SENDER_EMAIL,
                "name": settings.BREVO_SENDER_NAME,
            },
            "to": [{"email": to}],
            "subject": subject,
            "htmlContent": html_content,
        }

        headers = {
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
            except httpx.RequestError:
                raise EmailServiceUnavailableError()

        if response.status_code < 400:
            logger.info(
                "Brevo email sent successfully",
                extra={
                    "recipient": to,
                    "status_code": response.status_code,
                    "response": response.text[:500],
                },
            )

        if response.status_code >= 400:
            logger.error(
                "Brevo email send failed",
                extra={
                    "recipient": to,
                    "status_code": response.status_code,
                    "response": response.text[:500],
                },
            )
            raise EmailSentFailedError()
