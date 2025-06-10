from backend_patcher import BackendPatcher
from cyberham.backend.users import leaderboard
from cyberham.database.types import User
from cyberham.tests.models import users, events, attendance, points
from cyberham.utils.date import current_semester, current_year


class TestLeaderboard(BackendPatcher):
    def setup_method(self):
        self.initial_users = users()
        self.initial_events = events()
        self.initial_attendance = attendance()
        self.initial_points = points()
        super().setup_method()

    def test_points(self):
        got = leaderboard("points", len(users()))
        expected = self._get_expected_points()

        assert got == expected, "Attended users should be correctly sorted"

    def test_attended(self):
        got = leaderboard("attended", len(users()))
        expected = self._get_expected_attendance()

        assert got == expected, "Attended users should be correctly sorted"

    def test_limit(self):
        limit = 2

        got = leaderboard("points", limit)
        expected = self._get_expected_points()

        assert got == expected[:limit], "List should be correctly truncated"

    def _get_expected_points(self):
        semester = current_semester()
        year = current_year()

        # Index points from attendance for the relevant semester/year
        event_map = {
            event["code"]: event
            for event in events()
            if event["semester"] == semester and event["year"] == year
        }

        attendance_points: dict[int, int] = {}
        for record in attendance():
            code = record["code"]
            if code in event_map:
                user_id = record["user_id"]
                attendance_points[user_id] = (
                    attendance_points.get(user_id, 0) + event_map[code]["points"]
                )

        expected: list[tuple[User, int]] = []
        for user in users():
            uid = user["user_id"]
            base_points = next(
                (
                    p["points"]
                    for p in points()
                    if p["user_id"] == uid
                    and p["semester"] == semester
                    and p["year"] == year
                ),
                0,
            )
            extra_points = attendance_points.get(uid, 0)
            total_points = base_points + extra_points
            if total_points > 0:
                expected.append((user, total_points))

        expected.sort(key=lambda tup: tup[1], reverse=True)
        return expected

    def _get_expected_attendance(self):
        semester = current_semester()
        year = current_year()

        # Get valid event codes for this semester/year
        valid_codes = {
            event["code"]
            for event in events()
            if event["semester"] == semester and event["year"] == year
        }

        # Count attendance for each user, filtering by valid event codes
        attendance_count: dict[int, int] = {}
        for record in attendance():
            if record["code"] in valid_codes:
                uid = record["user_id"]
                attendance_count[uid] = attendance_count.get(uid, 0) + 1

        expected: list[tuple[User, int]] = []
        for user in users():
            count = attendance_count.get(user["user_id"], 0)
            if count > 0:
                expected.append((user, count))

        expected.sort(key=lambda x: x[1], reverse=True)
        return expected
