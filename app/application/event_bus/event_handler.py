from abc import ABC, abstractmethod


class EventHandler(ABC):
    @abstractmethod
    async def handle(self, event):
        pass
