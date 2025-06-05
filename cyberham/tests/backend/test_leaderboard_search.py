from backend_patcher import BackendPatcher
from cyberham.backend.users import leaderboard_search
from cyberham.tests.models import (
    users,
    valid_user,
    valid_user_2,
    events,
    attended_event,
    valid_event,
    unregistered_event,
)


class TestLeaderboardSearch(BackendPatcher):
    def setup_method(self):
        self.initial_users = users
        self.initial_events = events
        super().setup_method()

    def test_ranking(self):
        attended = leaderboard_search(attended_event["name"])

        expected: list[tuple[str, int]] = []
        for user in users:
            if user == valid_user or user == valid_user_2:
                expected.append((user["name"], 2))
            else:
                expected.append((user["name"], 1))
        expected.sort(key=lambda tup: tup[1], reverse=True)

        assert attended == expected

    def test_no_attendance(self):
        attended = leaderboard_search(valid_event["name"])
        assert attended == []

    def test_no_matching_activity(self):
        attended = leaderboard_search(unregistered_event["name"])
        assert attended == []
