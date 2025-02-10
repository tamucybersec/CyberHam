from cyberham.dynamodb.dynamo import DynamoDB
from cyberham.dynamodb.types import (
    TableName,
    MaybeEvent,
    Event,
    UpdateEvent,
    data_to_item,
    item_to_data,
    Key,
)


class EventsDB:
    db: DynamoDB
    table: TableName = "events"

    def __init__(self) -> None:
        self.db = DynamoDB()

    def put_event(self, event: Event) -> None:
        item = data_to_item(event)

        if item is None:
            raise TypeError(
                "This code is impossible to reach but the compiler demands I write it."
            )

        self.db.put_item(self.table, item)

    def get_event(self, event_code: str) -> MaybeEvent:
        key = self._get_key(event_code)
        item = self.db.get_item(self.table, key)
        return item_to_data(item, Event)

    def update_event(self, event_code: str, update: UpdateEvent) -> MaybeEvent:
        """
        Access an event, change its contents, and the upload the change.
        The accessed event can be None (the event doesn't exist) and you can return None (delete the event).
        Returns the updated event.
        """

        get_event = self.get_event(event_code)
        updated_event = update(get_event)

        if updated_event is None:
            self.delete_event(event_code)
            return None
        else:
            self.put_event(updated_event)
            return updated_event

    def delete_event(self, event_code: str) -> MaybeEvent:
        """
        Returns the event that was deleted.
        """

        key = self._get_key(event_code)
        item = self.db.delete_item(self.table, key)
        return item_to_data(item, Event)

    def get_all(self) -> list[Event]:
        items = self.db.get_all(self.table)

        events: list[Event] = []
        for item in items:
            events.append(item_to_data(item, Event))  # type: ignore

        return events

    def get_count(self) -> int:
        return len(self.db.get_all_raw(self.table))

    def _get_key(self, event_code: str) -> Key:
        return self.db.create_key("events", event_code)


eventsdb = EventsDB()
