from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.application.notifications.handlers.send_deposit_confirmation_email import (
    SendDepositConfirmationEmailHandler,
)
from app.core.exceptions.services import EmailServiceUnavailableError
from app.core.types.appointment_enums import AppointmentType
from app.domain.studio.finances.events.send_deposit_confirmation_email import (
    SendDepositConfirmationEmailEvent,
)
from tests.fakes.fake_email_service import FakeEmailService


@pytest.mark.parametrize(
    ("appointment_type", "expected_procedure"),
    [
        (AppointmentType.TATTOO, "sua tattoo"),
        (AppointmentType.PIERCING, "seu piercing"),
    ],
)
async def test_send_deposit_confirmation_email(
    appointment_type,
    expected_procedure,
):
    event = SendDepositConfirmationEmailEvent(
        client_email="client@email.com",
        amount=Decimal("50.25"),
        appointment_type=appointment_type,
        start_at=datetime(2030, 1, 8, 13, 0, tzinfo=timezone.utc),
    )
    email_service = FakeEmailService()

    await SendDepositConfirmationEmailHandler(email_service).handle(event)

    assert len(email_service.sent_emails) == 1
    assert email_service.last_payload is not None
    assert email_service.last_payload["to"] == "client@email.com"
    assert email_service.last_payload["subject"] == "Parabéns, seu agendamento esta confirmado!"
    assert "R$ 50.25" in email_service.last_payload["html"]
    assert "08/01/2030" in email_service.last_payload["html"]
    assert "13:00" in email_service.last_payload["html"]
    assert expected_procedure in email_service.last_payload["html"]


async def test_send_deposit_confirmation_email_propagates_service_failure():
    event = SendDepositConfirmationEmailEvent(
        client_email="client@email.com",
        amount=Decimal("50"),
        appointment_type=AppointmentType.TATTOO,
        start_at=datetime(2030, 1, 8, 13, 0, tzinfo=timezone.utc),
    )
    email_service = FakeEmailService(fail_with="email_service_unavailable")

    with pytest.raises(EmailServiceUnavailableError):
        await SendDepositConfirmationEmailHandler(email_service).handle(event)

    assert email_service.sent is False
