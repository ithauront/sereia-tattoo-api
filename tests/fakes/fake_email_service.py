from typing import TypedDict

from app.application.notifications.ports.email_service import EmailService
from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
)


class EmailPayload(TypedDict):
    to: str
    subject: str
    html: str


class FakeEmailService(EmailService):
    def __init__(self, *, fail_with: str | None = None) -> None:
        self.fail_with = fail_with
        self.sent = False
        self.last_payload: EmailPayload | None = None

    async def send_email(self, to, subject, html_content):
        if self.fail_with == "email_service_unavailable":
            raise EmailServiceUnavailableError()
        if self.fail_with == "email_send_failed":
            raise EmailSentFailedError()

        self.sent = True
        self.last_payload = {
            "to": to,
            "subject": subject,
            "html": html_content,
        }
