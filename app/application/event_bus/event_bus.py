from collections import defaultdict
from typing import Type


class EventBus:
    def __init__(self):
        self._handlers = defaultdict(list)

    def register(self, event_type: Type, handler):
        self._handlers[event_type].append(handler)
