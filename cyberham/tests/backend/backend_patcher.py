from cyberham.apis.google_apis import google
from cyberham.apis.mock_google_apis import MockGoogleClient
from cyberham.database.typeddb import (
    T,
    TypedDB,
    db,
    usersdb,
    eventsdb,
    flaggeddb,
    attendancedb,
    pointsdb,
)
from cyberham.database.types import User, Event, Flagged, Attendance, Points, TableName
from cyberham.apis.types import EmailPending


class BackendPatcher:
    initial_users: list[User] = []
    initial_events: list[Event] = []
    initial_flagged: list[Flagged] = []
    initial_attendance: list[Attendance] = []
    initial_points: list[Points] = []
    initial_pending: list[EmailPending] = []

    google_client: MockGoogleClient

    def setup_method(self):
        # create a temporary, in-memory database for testing
        db.setup(":memory:")

        tables: list[TableName] = ["users", "events", "flagged", "attendance", "points"]
        for table in tables:
            db.reset_table(table)

        self.set_initial(usersdb, self.initial_users)
        self.set_initial(eventsdb, self.initial_events)
        self.set_initial(flaggeddb, self.initial_flagged)
        self.set_initial(attendancedb, self.initial_attendance)
        self.set_initial(pointsdb, self.initial_points)

        self.google_client = MockGoogleClient(self.initial_pending)
        google.client = self.google_client

    def set_initial(self, typeddb: TypedDB[T], initial: list[T]):
        for init in initial:
            typeddb.create(init)
