import json
from httpx import Response
import httpx
import pytest
import respx

from app.core.exceptions.services import (
    EmailSentFailedError,
    EmailServiceUnavailableError,
)
from app.infrastructure.email.brevo_email_service import BrevoEmailService


@respx.mock
async def test_brevo_email_service_send_successfully():
    route = respx.post("https://api.brevo.com/v3/smtp/email").mock(
        return_value=Response(201, json={"messageId": "123"})
    )

    service = BrevoEmailService()

    result = await service.send_email(
        to="jhon@doe.com",
        subject="teste",
        html_content="<p>Hello</p>",
    )

    assert result is None
    assert route.called
    assert route.calls.call_count == 1

    request = route.calls[0].request
    body = json.loads(request.content.decode())

    assert request.headers["Content-Type"] == "application/json"
    assert body["to"][0]["email"] == "jhon@doe.com"
    assert body["subject"] == "teste"
    assert body["htmlContent"] == "<p>Hello</p>"


@respx.mock
async def test_brevo_email_service_unrechable():
    respx.post("https://api.brevo.com/v3/smtp/email").mock(
        side_effect=httpx.RequestError("Connection error")
    )

    service = BrevoEmailService()

    with pytest.raises(EmailServiceUnavailableError):
        await service.send_email(
            to="jhon@doe.com",
            subject="Teste",
            html_content="<p>Hello</p>",
        )


@respx.mock
async def test_brevo_email_service_raises_on_error():
    respx.post("https://api.brevo.com/v3/smtp/email").mock(
        return_value=Response(500, text="error")
    )

    service = BrevoEmailService()

    with pytest.raises(EmailSentFailedError):
        await service.send_email(
            to="jhon@doe.com",
            subject="Teste",
            html_content="<p>Hello</p>",
        )
