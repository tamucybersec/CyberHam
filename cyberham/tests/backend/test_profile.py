from backend_patcher import BackendPatcher
from cyberham.backend.users import profile
from cyberham.tests.models import users, valid_user, unregistered_user


class TestProfile(BackendPatcher):
    def setup_method(self):
        self.initial_users = users()
        super().setup_method()

    def test_valid_user(self):
        res = profile(valid_user()["user_id"])
        assert res[0] == ""
        assert res[1] == valid_user()

    def test_unregistered_user(self):
        res = profile(unregistered_user()["user_id"])
        assert res[0] != ""
        assert res[1] is None
