from enum import Enum


class PaymentMethodType(str, Enum):
    CASH = "cash"
    CARD = "card"
    PIX = "pix"
    CLIENT_CREDIT = "client_credit"


class PaymentPurposeType(str, Enum):
    APPOINTMENT = "appointment"
    DEPOSIT = "deposit"
    TIP = "tip"
    OTHER = "other"
