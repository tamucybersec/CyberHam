from backend_patcher import BackendPatcher
from cyberham.backend.events import find_event
from cyberham.tests.models import users, events, valid_event, unregistered_event


class TestFindEvent(BackendPatcher):
    def setup_method(self):
        self.initial_users = users
        self.initial_events = events
        super().setup_method()

    def test_valid_event(self):
        res = find_event(valid_event["code"])
        assert res[0] == ""
        assert res[1] == valid_event

    def test_unregistered_event(self):
        res = find_event(unregistered_event["code"])
        assert res[0] != ""
        assert res[1] is None

    def test_invalid_code(self):
        res = find_event("")
        assert res[0] != ""
        assert res[1] is None
