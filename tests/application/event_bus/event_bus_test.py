import asyncio

import pytest

from app.application.event_bus.integration_event_bus import IntegrationEventBus
from app.application.event_bus.transactional_event_bus import TransactionalEventBus


@pytest.mark.asyncio
@pytest.mark.parametrize("provide_uow", [False, True])
async def test_integration_event_bus_dispatch(read_uow, provide_uow):
    bus = IntegrationEventBus()

    handled = False
    expected_uow = read_uow if provide_uow else None

    class TestHandler:
        async def handle(self, event, *, uow=None):
            nonlocal handled
            assert uow is expected_uow
            handled = True

    class TestEvent:
        pass

    bus.register(TestEvent, TestHandler())

    if provide_uow:
        await bus.publish(TestEvent(), uow=read_uow)
    else:
        await bus.publish(TestEvent())

    assert not handled

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
