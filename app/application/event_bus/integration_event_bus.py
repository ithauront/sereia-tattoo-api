import asyncio

from app.application.event_bus.event_bus import EventBus


class IntegrationEventBus(EventBus):
    async def publish(self, event):
        handlers = self._handlers[type(event)]

        for handler in handlers:
            asyncio.create_task(handler.handle(event))
