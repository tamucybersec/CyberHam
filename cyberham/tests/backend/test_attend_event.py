from copy import deepcopy
from backend_patcher import BackendPatcher
from cyberham.backend import attend_event
from cyberham.tests.models import (
    valid_user,
    unregistered_user,
    valid_event,
    past_event,
    future_event,
    attended_event,
    unregistered_event,
    events
)


class TestAttendEvent(BackendPatcher):
    def setup_method(self):
        self.initial_users = [valid_user]
        self.initial_events = events
        super().setup_method()

    def test_successful(self):
        user = deepcopy(valid_user)
        event = deepcopy(valid_event)

        user["points"] += event["points"]
        user["attended"] += 1
        event["attended_users"].append(user["user_id"])

        msg, ev = attend_event(event["code"], user["user_id"])
        db_user = self.usersdb.get(user["user_id"])
        db_event = self.eventsdb.get(event["code"])

        assert msg, "String should be neither None nor empty"
        assert ev, "Event should not be None"
        assert ev == db_event, "Returned event should be the same as stored event"
        assert event == db_event, "Event attributes should be correctly updated"
        assert user == db_user, "User attributes should be correctly updated"

    def test_unregistered_user(self):
        user = deepcopy(unregistered_user)
        event = deepcopy(valid_event)

        msg, ev = attend_event(event["code"], user["user_id"])

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"

    def test_non_existent_event(self):
        user = deepcopy(valid_user)
        event = deepcopy(unregistered_event)

        msg, ev = attend_event(event["code"], user["user_id"])

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"

    def test_already_redeemed(self):
        user = deepcopy(valid_user)
        event = deepcopy(attended_event)

        msg, ev = attend_event(event["code"], user["user_id"])

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"

    def test_not_same_day_past(self):
        user = deepcopy(valid_user)
        event = deepcopy(past_event)

        msg, ev = attend_event(event["code"], user["user_id"])

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"

    def test_not_same_day_future(self):
        user = deepcopy(valid_user)
        event = deepcopy(future_event)

        msg, ev = attend_event(event["code"], user["user_id"])

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"
