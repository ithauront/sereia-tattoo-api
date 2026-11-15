from uuid import uuid4

import pytest

from app.core.exceptions.validation import ValidationError
from app.core.types.client_credit_source_type import (
    ClientCreditSourceType,
)
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry


def test_source_type_unknown_raises_error():
    with pytest.raises(ValidationError) as exc:
        ClientCreditEntry(
            vip_client_id=uuid4(),
            source_id=uuid4(),
            source_type="unknown_source_type",
            quantity=1,
        )

    assert "Invalid value" in str(exc.value)


def test_source_type_correct_not_enum_success(make_client_credit_entry):
    entry = make_client_credit_entry(source_type="used_as_payment")

    assert entry.source_type == ClientCreditSourceType.USED_AS_PAYMENT


def test_source_type_enum_success(make_client_credit_entry):
    entry = make_client_credit_entry(source_type=ClientCreditSourceType.INDICATION)

    assert entry.source_type == ClientCreditSourceType.INDICATION


def test_cancellation_credit_records_original_payment_and_creation_time():
    from datetime import datetime, timezone

    vip_id, payment_id = uuid4(), uuid4()
    created_at = datetime(2030, 1, 1, tzinfo=timezone.utc)
    entry = ClientCreditEntry.create_credits_from_cancellation(
        vip_client_id=vip_id, payment_id=payment_id, quantity=150, created_at=created_at
    )

    assert entry.vip_client_id == vip_id
    assert entry.source_id == payment_id
    assert entry.source_type == ClientCreditSourceType.APPOINTMENT_CANCELLATION
    assert entry.quantity == 150
    assert entry.is_credit is True
    assert entry.is_debit is False
    assert entry.related_entry_id is None
    assert entry.created_at == created_at
    assert entry.reason == "Créditos referentes à caução de agendamento cancelado."


@pytest.mark.parametrize("quantity", [0, -1])
def test_cancellation_credit_rejects_non_positive_quantity(quantity):
    from app.core.exceptions.marketing import CreditMustBePositiveError

    with pytest.raises(CreditMustBePositiveError):
        ClientCreditEntry.create_credits_from_cancellation(
            vip_client_id=uuid4(), payment_id=uuid4(), quantity=quantity
        )


@pytest.mark.parametrize(
    "source_type",
    [ClientCreditSourceType.APPOINTMENT_CANCELLATION, "appointment_cancellation"],
)
def test_cancellation_credit_fixture_supports_enum_and_serialized_value(
    make_client_credit_entry, source_type
):
    from datetime import datetime, timezone

    payment_id = uuid4()
    created_at = datetime(2030, 1, 1, tzinfo=timezone.utc)
    entry = make_client_credit_entry(
        source_type=source_type, source_id=payment_id, quantity=200, created_at=created_at
    )
    assert entry.source_type == ClientCreditSourceType.APPOINTMENT_CANCELLATION
    assert entry.source_type.value == "appointment_cancellation"
    assert entry.source_id == payment_id
    assert entry.quantity == 200
    assert entry.created_at == created_at
