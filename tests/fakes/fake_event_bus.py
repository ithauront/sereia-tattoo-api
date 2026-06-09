from app.application.event_bus.transactional_event_bus import TransactionalEventBus


class FakeTransactionalEventBus(TransactionalEventBus):
    def __init__(self):
        self.events = []

    async def publish(self, event, **context):
        self.events.append(event)


class FakeIntegrationEventBus:
    def __init__(self):
        self.events = []

    async def publish(self, event, **context):
        self.events.append(event)
