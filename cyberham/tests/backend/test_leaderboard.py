from pytest import MonkeyPatch
from cyberham.tests.backend.mockdb import MockDB
from cyberham.backend import leaderboard
from cyberham.tests.backend.models import users


class TestLeaderboard:
    def setup_method(self):
        mp = MonkeyPatch()
        self.usersdb = MockDB(users, "user_id", None)
        mp.setattr("cyberham.backend.usersdb", self.usersdb)

    def test_points(self):
        got = leaderboard("points", len(users))
        expected = sorted(users, key=lambda user: user["points"], reverse=True)

        assert got == expected, "Attended users should be correctly sorted"

    def test_attended(self):
        got = leaderboard("attended", len(users))
        expected = sorted(users, key=lambda user: user["attended"], reverse=True)

        assert got == expected, "Attended users should be correctly sorted"

    def test_limit(self):
        limit = 2

        got = leaderboard("points", limit)
        expected = sorted(users, key=lambda user: user["points"], reverse=True)

        assert got == expected[:limit], "List should be correctly truncated"
