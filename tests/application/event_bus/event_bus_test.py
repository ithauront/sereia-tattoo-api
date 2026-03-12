import pytest

from app.application.event_bus.event_bus import EventBus


@pytest.mark.asyncio
async def test_event_bus_dispatch():

    bus = EventBus()

    handled = False

    class TestHandler:
        async def handle(self, event):
            nonlocal handled
            handled = True

    class TestEvent:
        pass

    bus.register(TestEvent, TestHandler())

    await bus.publish(TestEvent())

    assert handled
