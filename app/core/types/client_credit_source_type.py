from enum import Enum


# TODO(migration): incluir APPOINTMENT_CANCELLATION no enum PostgreSQL existente.
class ClientCreditSourceType(str, Enum):
    INDICATION = "indication"
    ADDED_BY_ADMIN = "added_by_admin"
    APPOINTMENT_CANCELLATION = "appointment_cancellation"
    USED_AS_PAYMENT = "used_as_payment"
    REVERSED_BY_ADMIN = "reversed_by_admin"
