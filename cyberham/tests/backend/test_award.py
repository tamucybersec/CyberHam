from backend_patcher import BackendPatcher
from cyberham.backend.users import award
from cyberham.tests.models import (
    users,
    valid_user,
    unregistered_user,
)
from cyberham.utils.date import current_semester, current_year
from cyberham.database.typeddb import pointsdb


class TestAward(BackendPatcher):
    def setup_method(self):
        self.initial_users = users()
        super().setup_method()

    def test_valid_user(self):
        user = valid_user()
        points = 2000

        points_before = pointsdb.get(
            (user["user_id"], current_semester(), current_year())
        )
        assert points_before is None

        res = award(user["user_id"], user["name"], points)
        assert res != ""

        points_after = pointsdb.get(
            (user["user_id"], current_semester(), current_year())
        )
        assert points_after is not None
        assert points_after["points"] == points

    def test_invalid_user(self):
        user = unregistered_user()
        points = 2000

        res = award(user["user_id"], user["name"], points)
        assert res != ""

        assert (
            pointsdb.get((user["user_id"], current_semester(), current_year())) is None
        )

    def test_pointed_user(self):
        # TODO
        pass
