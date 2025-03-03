from pytest import MonkeyPatch
from cyberham.apis.mock_google_apis import MockGoogleClient
from cyberham.dynamodb.mockdb import MockDB
from cyberham.dynamodb.types import User, Event, Flagged


class BackendPatcher:
    initial_users: list[User] = []
    initial_events: list[Event] = []
    initial_flagged: list[Flagged] = []

    usersdb: MockDB[User]
    eventsdb: MockDB[Event]
    flaggeddb: MockDB[Flagged]

    google_client: MockGoogleClient

    def setup_method(self):
        self.mp = MonkeyPatch()

        self.usersdb = MockDB(self.initial_users, "user_id", None)
        self.mp.setattr("cyberham.backend.usersdb", self.usersdb)

        self.eventsdb = MockDB(self.initial_events, "code", None)
        self.mp.setattr("cyberham.backend.eventsdb", self.eventsdb)

        self.flaggeddb = MockDB(self.initial_flagged, "user_id", None)
        self.mp.setattr("cyberham.backend.flaggeddb", self.flaggeddb)

        self.google_client = MockGoogleClient()
        self.mp.setattr("cyberham.backend.google_client", self.google_client)
