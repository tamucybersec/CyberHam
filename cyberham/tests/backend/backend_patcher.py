from pytest import MonkeyPatch
from cyberham.dynamodb.mockdb import MockDB
from cyberham.dynamodb.types import User, Event, Flagged


class BackendPatcher:
    initial_users: list[User] | None = None
    initial_events: list[Event] | None = None
    initial_flagged: list[Flagged] | None = None

    usersdb: MockDB[User]
    eventsdb: MockDB[Event]
    flaggeddb: MockDB[Flagged]

    def setup_method(self):
        self.mp = MonkeyPatch()

        if self.initial_users:
            self.usersdb = MockDB(self.initial_users, "user_id", None)
            self.mp.setattr("cyberham.backend.usersdb", self.usersdb)

        if self.initial_events:
            self.eventsdb = MockDB(self.initial_events, "code", None)
            self.mp.setattr("cyberham.backend.eventsdb", self.eventsdb)

        if self.initial_flagged:
            self.flaggeddb = MockDB(self.initial_flagged, "user_id", None)
            self.mp.setattr("cyberham.backend.flaggeddb", self.flaggeddb)
