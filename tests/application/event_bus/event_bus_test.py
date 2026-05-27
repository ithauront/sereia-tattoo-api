import asyncio

import pytest

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.event_bus.transactional_event_bus import TransactionalEventBus


@pytest.mark.asyncio
async def test_integration_event_bus_dispatch():
    bus = IntegrationEventBus()

    handled = False

    class TestHandler:
        async def handle(self, event):
            nonlocal handled
            handled = True

    class TestEvent:
        pass

    bus.register(TestEvent, TestHandler())

    await bus.publish(TestEvent())

    await asyncio.sleep(0)

    assert handled


@pytest.mark.asyncio
async def test_transactional_event_bus_dispatch():
    bus = TransactionalEventBus()

    handled = False

    class TestHandler:
        async def handle(self, event, uow=None):
            nonlocal handled
            handled = True

    class TestEvent:
        pass

    bus.register(TestEvent, TestHandler())

    await bus.publish(TestEvent(), uow={})

    assert handled
