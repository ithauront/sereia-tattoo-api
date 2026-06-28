from abc import ABC, abstractmethod


class EmailService(ABC):
    @abstractmethod
    async def send_email(self, to: str, subject: str, html_content: str) -> None: ...
