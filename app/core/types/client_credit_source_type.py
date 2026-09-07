from enum import Enum


class ClientCreditSourceType(str, Enum):
    INDICATION = "indication"
    ADDED_BY_ADMIN = "added_by_admin"
    USED_AS_PAYMENT = "used_as_payment"
    REVERSED_BY_ADMIN = "reversed_by_admin"
