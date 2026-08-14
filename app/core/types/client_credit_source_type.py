from enum import Enum


class ClientCreditSourceType(str, Enum):
    INDICATION = "indication"
    ADDED_BY_ADMIN = "added_by_admin"
    USED_HAS_PAYMENT = "used_has_payment"
    REVERSED_BY_ADMIN = "reversed_by_admin"
