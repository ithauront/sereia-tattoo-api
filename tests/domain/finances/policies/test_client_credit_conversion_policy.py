from decimal import Decimal

import pytest

from app.core.exceptions.payment import PaymentConsumesZeroClientCreditsError
from app.domain.studio.finances.policies.client_credit_conversion_policy import (
    ClientCreditConversionPolicy,
)


@pytest.mark.parametrize(
    ("amount", "expected_credits"),
    [
        (Decimal("1.00"), 1),
        (Decimal("10.00"), 10),
        (Decimal("10.99"), 10),
    ],
)
def test_credits_to_consume_rounds_down(amount, expected_credits):
    assert ClientCreditConversionPolicy.credits_to_consume(amount) == expected_credits


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("0.01"), Decimal("0.99")])
def test_credits_to_consume_rejects_zero_credit_result(amount):
    with pytest.raises(PaymentConsumesZeroClientCreditsError):
        ClientCreditConversionPolicy.credits_to_consume(amount)
