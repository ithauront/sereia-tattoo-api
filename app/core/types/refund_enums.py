from enum import Enum

"""
Client credit should be the default refund method whenever possible.

Other refund methods exist to support situations where
the client explicitly requests another form of refund.
"""


class RefundMethodType(str, Enum):
    CASH = "cash"
    CARD = "card"
    PIX = "pix"
    CLIENT_CREDIT = "client_credit"


"""
For now we will always use status completed since refund will be manual
But if one day we automate refunds we may want to have refund status
"""


class RefundStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
