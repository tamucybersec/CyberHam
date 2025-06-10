from backend_patcher import BackendPatcher
from cyberham.backend.events import attend_event
from cyberham.tests.models import (
    valid_user,
    unregistered_user,
    users,
    valid_event,
    past_event,
    future_event,
    attended_event,
    unregistered_event,
    events,
    attendance,
)
from cyberham.database.typeddb import attendancedb


class TestAttendEvent(BackendPatcher):
    def setup_method(self):
        self.initial_users = users()
        self.initial_events = events()
        self.initial_attendance = attendance()
        super().setup_method()

    def test_successful(self):
        user = valid_user()
        event = valid_event()

        msg, ev = attend_event(event["code"], user["user_id"])
        attendance = attendancedb.get((user["user_id"], event["code"]))

        assert msg, "String should be neither None nor empty"
        assert ev, "Event should not be None"
        assert ev == event, "Returned event should be the same as original event"
        assert attendance is not None

    def test_unregistered_user(self):
        user = unregistered_user()
        event = valid_event()

        msg, ev = attend_event(event["code"], user["user_id"])
        attendance = attendancedb.get((user["user_id"], event["code"]))

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"
        assert attendance is None

    def test_non_existent_event(self):
        user = valid_user()
        event = unregistered_event()

        msg, ev = attend_event(event["code"], user["user_id"])
        attendance = attendancedb.get((user["user_id"], event["code"]))

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"
        assert attendance is None

    def test_already_redeemed(self):
        user = valid_user()
        event = attended_event()

        msg, ev = attend_event(event["code"], user["user_id"])

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"

    def test_not_same_day_past(self):
        user = valid_user()
        event = past_event()

        msg, ev = attend_event(event["code"], user["user_id"])
        attendance = attendancedb.get((user["user_id"], event["code"]))

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"
        assert attendance is None

    def test_not_same_day_future(self):
        user = valid_user()
        event = future_event()

        msg, ev = attend_event(event["code"], user["user_id"])
        attendance = attendancedb.get((user["user_id"], event["code"]))

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"
        assert attendance is None
