from decimal import ROUND_FLOOR, Decimal

from app.core.exceptions.payment import PaymentConsumesZeroClientCreditsError


class ClientCreditConversionPolicy:
    @staticmethod
    def credits_to_consume(amount: Decimal) -> int:
        credits = int(amount.to_integral_value(rounding=ROUND_FLOOR))

        if credits <= 0:
            raise PaymentConsumesZeroClientCreditsError()

        return credits
