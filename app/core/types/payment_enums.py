from enum import Enum


class PaymentMethodType(str, Enum):
    CASH = "cash"
    CARD = "card"
    PIX = "pix"
    CLIENT_CREDIT = "client_credit"
