from backend_patcher import BackendPatcher
from cyberham.backend import leaderboard
from cyberham.tests.models import users


class TestLeaderboard(BackendPatcher):
    def setup_method(self):
        self.initial_users = users
        super().setup_method()

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
