class FakeEmailService:
    def __init__(self):
        self.sent = False
        self.last_payload = None

    async def send_email(self, to, subject, html_content):
        self.sent = True
        self.last_payload = {
            "to": to,
            "subject": subject,
            "html": html_content,
        }
