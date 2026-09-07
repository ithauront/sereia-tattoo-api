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
