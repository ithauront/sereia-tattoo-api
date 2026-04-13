import re

from app.core.exceptions.validation import InvalidClientCode


class ClientCode:
    def __init__(self, value: str):
        value = value.strip().upper()
        """
            Regex para str de maiusculos
            seguido de hifen
            seguido de outra str de maiusculos
            seguido de opcional hifen e dois digitos
        """
        if not re.match(r"^[A-Z]+-[A-Z]+(-\d{2})?$", value):

            raise InvalidClientCode("invalid_client_code_format")

        self.value = value

    def __str__(self):
        return self.value
