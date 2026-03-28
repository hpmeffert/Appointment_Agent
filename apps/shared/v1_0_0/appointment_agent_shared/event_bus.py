from .contracts import EventEnvelope


class InMemoryEventBus:
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    def publish(self, event: EventEnvelope) -> EventEnvelope:
        self.events.append(event)
        return event


event_bus = InMemoryEventBus()
