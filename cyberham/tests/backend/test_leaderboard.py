from pytest import MonkeyPatch
from cyberham.tests.backend.mockdb import MockDB
from cyberham.dynamodb.types import User
from cyberham.backend import leaderboard

users = [
    User(points=100, attended=5, user_id="0", name="Lane", grad_year=2024, email=""),
    User(points=200, attended=1, user_id="1", name="Colby", grad_year=2025, email=""),
    User(points=50, attended=50, user_id="2", name="Damian", grad_year=2026, email=""),
    User(points=0, attended=15, user_id="3", name="Stella", grad_year=2025, email=""),
    User(points=1000, attended=0, user_id="4", name="Ezra", grad_year=2027, email=""),
]


class TestLeaderboard:
    def setup_method(self):
        self.mp = MonkeyPatch()
        self.db = MockDB(users, "user_id", None)
        self.mp.setattr("cyberham.backend.usersdb", self.db)

    def teardown_method(self):
        self.mp.undo()

    def test_points(self):
        got = leaderboard("points")
        expected = sorted(users, key=lambda user: user["points"], reverse=True)

        assert got == expected

    def test_attended(self):
        got = leaderboard("attended")
        expected = sorted(users, key=lambda user: user["attended"], reverse=True)

        assert got == expected

    def test_limit(self):
        limit = 2

        got = leaderboard("points", limit)
        expected = sorted(users, key=lambda user: user["points"], reverse=True)

        assert got == expected[:limit]
