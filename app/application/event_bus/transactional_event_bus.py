import asyncio
from app.application.event_bus.event_bus import EventBus


class TransactionalEventBus(EventBus):
    async def publish(self, event, *, uow):
        handlers = self._handlers[type(event)]

        await asyncio.gather(*(handler.handle(event, uow=uow) for handler in handlers))
