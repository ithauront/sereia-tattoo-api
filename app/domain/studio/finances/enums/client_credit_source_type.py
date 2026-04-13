from enum import Enum


class ClientCreditSourceType(str, Enum):
    INDICATION = "indication"
    ADDED_BY_ADMIN = "added_by_admin"
    USED_IN_APPOINTMENT = "used_in_appointment"
    REVERSED_BY_ADMIN = "reversed_by_admin"
