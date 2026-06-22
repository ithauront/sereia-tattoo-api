import asyncio

from app.application.event_bus.event_bus import EventBus
from app.application.studio.unit_of_work.write_unit_of_work import WriteUnitOfWork


class TransactionalEventBus(EventBus):
    async def publish(self, event, *, uow: WriteUnitOfWork):
        handlers = self._handlers[type(event)]

        await asyncio.gather(*(handler.handle(event, uow=uow) for handler in handlers))
