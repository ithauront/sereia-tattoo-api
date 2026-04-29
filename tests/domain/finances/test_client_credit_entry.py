from uuid import uuid4

import pytest

from app.core.exceptions.validation import ValidationError
from app.domain.studio.finances.entities.client_credit_entry import ClientCreditEntry
from app.domain.studio.finances.enums.client_credit_source_type import (
    ClientCreditSourceType,
)


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
    entry = make_client_credit_entry(source_type="used_in_appointment")

    assert entry.source_type == ClientCreditSourceType.USED_IN_APPOINTMENT


def test_source_type_enum_success(make_client_credit_entry):
    entry = make_client_credit_entry(source_type=ClientCreditSourceType.INDICATION)

    assert entry.source_type == ClientCreditSourceType.INDICATION
