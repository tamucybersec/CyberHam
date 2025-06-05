from backend_patcher import BackendPatcher
from copy import deepcopy
from cyberham.backend.users import award
from cyberham.tests.models import (
    users,
    valid_user,
    unregistered_user,
)


class TestAward(BackendPatcher):
    def setup_method(self):
        self.initial_users = users
        super().setup_method()

    def test_valid_user(self):
        points = 2000
        user = deepcopy(valid_user)
        user["points"] += points

        res = award(user["user_id"], user["name"], points)
        assert res != ""

        got = self.usersdb.get([user["user_id"]])
        assert got == user

    def test_invalid_user(self):
        points = 2000
        user = deepcopy(unregistered_user)

        res = award(user["user_id"], user["name"], points)
        assert res != ""
        assert self.usersdb.get([unregistered_user["user_id"]]) is None
