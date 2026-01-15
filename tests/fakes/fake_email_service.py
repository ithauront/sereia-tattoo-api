from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
)


class FakeEmailService:
    def __init__(self, *, fail_with: str | None = None):
        self.fail_with = fail_with
        self.sent = False
        self.last_payload = None

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
