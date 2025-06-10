from backend_patcher import BackendPatcher
from cyberham.backend.events import find_event
from cyberham.tests.models import (
    users,
    events,
    valid_event,
    unregistered_event,
    attendance,
)


class TestFindEvent(BackendPatcher):
    def setup_method(self):
        self.initial_users = users
        self.initial_events = events
        self.initial_attendance = attendance
        super().setup_method()

    def test_valid_event(self):
        res, evt, att = find_event(valid_event["code"])
        assert res == ""
        assert evt == valid_event
        assert att == sum(
            [(1 if a["code"] == valid_event["code"] else 0) for a in attendance]
        )

    def test_unregistered_event(self):
        res, evt, att = find_event(unregistered_event["code"])
        assert res != ""
        assert evt is None
        assert att == 0

    def test_invalid_code(self):
        res, evt, att = find_event("")
        assert res != ""
        assert evt is None
        assert att == 0
