import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.notifications.handlers.send_password_reset_email import (
    SendPasswordResetEmailHandler,
)
from app.domain.studio.users.events.password_reset_email_requested import (
    PasswordResetEmailRequested,
)
from tests.fakes.fake_email_service import FakeEmailService
from tests.fakes.fake_versioned_token import FakeVersionedTokenService


async def test_send_password_reset_handler_sends_email():
    user_id = uuid4()
    event = PasswordResetEmailRequested(user_id=user_id, email="jhon@doe.com", password_token_version=1)

    email_service = FakeEmailService()
    token_service = FakeVersionedTokenService()

    handler = SendPasswordResetEmailHandler(email_service=email_service, token_service=token_service)

    await handler.handle(event)

    assert email_service.sent is True
    assert email_service.last_payload is not None

    assert email_service.last_payload["to"] == "jhon@doe.com"
    assert email_service.last_payload["subject"] == "Recuperação de senha"
    assert "fake-token" in email_service.last_payload["html"]


@pytest.mark.parametrize("provider_fails", [False, True])
async def test_password_reset_with_dispatch_without_typeerror_fallback(
    read_uow,
    monkeypatch,
    provider_fails,
):
    bus = IntegrationEventBus()
    tasks = []
    create_task = asyncio.create_task

    def capture_task(coroutine):
        task = create_task(coroutine)
        tasks.append(task)
        return task

    monkeypatch.setattr(asyncio, "create_task", capture_task)
    service = FakeEmailService()
    failure = TypeError("erro interno do serviço de email")
    send = AsyncMock(wraps=service.send_email)
    if provider_fails:
        send.side_effect = failure
    monkeypatch.setattr(service, "send_email", send)
    handler = SendPasswordResetEmailHandler(service, FakeVersionedTokenService())
    bus.register(PasswordResetEmailRequested, handler)
    event = PasswordResetEmailRequested(uuid4(), "client@example.com", 1)

    await bus.publish(event, uow=read_uow)

    assert len(tasks) == 1
    # publish continua fire-and-forget; o teste aguarda a tarefa para observar o resultado.
    if provider_fails:
        with pytest.raises(TypeError) as caught:
            await tasks[0]
        assert caught.value is failure
    else:
        await tasks[0]
        assert service.last_payload["to"] == "client@example.com"
        assert "fake-token" in service.last_payload["html"]
    send.assert_awaited_once()
