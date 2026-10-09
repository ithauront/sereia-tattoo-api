import asyncio

from app.application.event_bus.event_bus import EventBus
from app.application.studio.unit_of_work.read_unit_of_work import ReadUnitOfWork


class IntegrationEventBus(EventBus):
    async def publish(self, event, *, uow: ReadUnitOfWork | None = None):
        handlers = self._handlers[type(event)]

        for handler in handlers:
            asyncio.create_task(handler.handle(event, uow=uow))
