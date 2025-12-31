from abc import ABC, abstractmethod
from typing import Awaitable


class EmailService(ABC):
    @abstractmethod
    def send_email(
        self, to: str, subject: str, html_content: str
    ) -> Awaitable[None]: ...
