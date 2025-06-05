from pytest import MonkeyPatch
from cyberham.apis.mock_google_apis import MockGoogleClient
from cyberham.database.mockdb import MockDB
from cyberham.database.types import User, Event, Flagged
from cyberham.apis.types import EmailPending
from pathlib import Path


class BackendPatcher:
    initial_users: list[User] = []
    initial_events: list[Event] = []
    initial_flagged: list[Flagged] = []
    initial_pending: list[EmailPending] = []

    usersdb: MockDB[User]
    eventsdb: MockDB[Event]
    flaggeddb: MockDB[Flagged]
    google_client: MockGoogleClient

    # monkey patch the mock implementations over the real ones
    # some files don't import them, so they are skipped in that case
    def setup_method(self):
        self.mp = MonkeyPatch()

        self.usersdb = MockDB(self.initial_users, ["user_id"])
        self.eventsdb = MockDB(self.initial_events, ["code"])
        self.flaggeddb = MockDB(self.initial_flagged, ["user_id"])
        self.google_client = MockGoogleClient(self.initial_pending)

        files = [f.stem for f in Path("cyberham/backend").iterdir() if f.is_file()]
        for file in files:
            self._attempt_patch(f"cyberham.backend.{file}.usersdb", self.usersdb)
            self._attempt_patch(f"cyberham.backend.{file}.eventsdb", self.eventsdb)
            self._attempt_patch(f"cyberham.backend.{file}.flaggeddb", self.flaggeddb)
            self._attempt_patch(
                f"cyberham.backend.{file}.google_client", self.google_client
            )

    def _attempt_patch(self, path: str, attr: object):
        try:
            self.mp.setattr(path, attr)
        except:
            pass
