from pytest import MonkeyPatch
from cyberham.tests.backend.mockdb import MockDB
from cyberham.backend import attend_event
from cyberham.tests.backend.models import valid_user, no_grad_year_user, unregistered_user, current_event, events
from copy import deepcopy


class TestAttendEvent:
    def setup_method(self):
        mp = MonkeyPatch()
        self.usersdb = MockDB([valid_user, no_grad_year_user], "user_id", None)
        self.eventsdb = MockDB(events, "code", None)
        mp.setattr("cyberham.backend.usersdb", self.usersdb)
        mp.setattr("cyberham.backend.eventsdb", self.eventsdb)

    def test_successful(self):
        user = deepcopy(valid_user)
        event = deepcopy(current_event)

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
        event = deepcopy(current_event)

        msg, ev = attend_event(event["code"], user["user_id"])

        assert msg, "String should be neither None nor empty"
        assert ev is None, "No event should be returned"

    def test_non_existent_event(self):
        assert False

    def test_already_redeemed(self):
        assert False

    def test_not_same_day(self):
        assert False
