from backend_patcher import BackendPatcher
from cyberham.backend.users import leaderboard_search
from cyberham.tests.models import (
    users,
    events,
    attended_event,
    valid_event,
    unregistered_event,
    attendance,
)


class TestLeaderboardSearch(BackendPatcher):
    def setup_method(self):
        self.initial_users = users()
        self.initial_events = events()
        self.initial_attendance = attendance()
        super().setup_method()

    def test_ranking(self):
        got = leaderboard_search(attended_event()["name"])

        matching_codes = [
            e["code"]
            for e in events()
            if attended_event()["name"].lower() in e["name"].lower()
        ]

        # Count how many matching events each user attended
        user_counts: dict[int, int] = {}
        for record in attendance():
            if record["code"] in matching_codes:
                user_id = record["user_id"]
                user_counts[user_id] = user_counts.get(user_id, 0) + 1

        expected: list[tuple[str, int]] = []
        for user in users():
            count = user_counts.get(user["user_id"], 0)
            if count == 0:
                continue
            expected.append((user["name"], count))
        expected.sort(key=lambda tup: tup[1], reverse=True)

        print(got, "\n\n", expected)

        assert got == expected

    def test_no_attendance(self):
        attended = leaderboard_search(valid_event()["name"])
        assert attended == []

    def test_no_matching_activity(self):
        attended = leaderboard_search(unregistered_event()["name"])
        assert attended == []
