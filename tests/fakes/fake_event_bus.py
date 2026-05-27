class FakeTransactionalEventBus:
    def __init__(self):
        self.events = []

    async def publish(self, event, **context):
        self.events.append(event)


class FakeIntegrationEventBus:
    def __init__(self):
        self.events = []

    async def publish(self, event, **context):
        self.events.append(event)
