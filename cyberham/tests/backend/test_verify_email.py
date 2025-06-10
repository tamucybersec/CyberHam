from backend_patcher import BackendPatcher
from cyberham.backend.register import verify_email
from cyberham.database.types import User
from cyberham.tests.models import (
    users,
    valid_user,
    valid_user_2,
    flagged_user,
    unregistered_user,
    flagged_users,
    extended_pending_users,
    VERIFICATION_CODE,
    NEW_EMAIL,
)
from cyberham.database.typeddb import usersdb


class TestVerifyEmail(BackendPatcher):
    def setup_method(self):
        self.initial_users = users()
        self.initial_flagged = flagged_users()
        self.initial_pending = extended_pending_users()
        super().setup_method()

    def test_verify_email(self):
        self._assert_working(valid_user())

    def test_flagged_user(self):
        self._assert_working(flagged_user())

    def _assert_working(self, user: User):
        res = verify_email(VERIFICATION_CODE, user["user_id"])
        assert res != ""

        assert (
            self.google_client.has_pending_email(user["user_id"]) == False
        ), "Should remove pending email"

        u = usersdb.get([user["user_id"]])
        assert u is not None
        assert u["email"] == NEW_EMAIL

    def test_unregistered_user(self):
        res = verify_email(VERIFICATION_CODE, unregistered_user()["user_id"])
        assert res != ""

        user = usersdb.get([unregistered_user()["user_id"]])
        assert user is None, "Should not create user"

        assert (
            self.google_client.has_pending_email(unregistered_user()["user_id"])
            == False
        ), "Should not create pending email"

    def test_no_pending(self):
        res = verify_email(VERIFICATION_CODE, valid_user_2()["user_id"])
        assert res != ""

        user = usersdb.get([valid_user_2()["user_id"]])
        assert user is not None
        assert user["email"] == user["email"], "Should not change email"

        assert (
            self.google_client.has_pending_email(valid_user_2()["user_id"]) == False
        ), "Should not create pending email"

    def test_verify_incorrect_code(self):
        res = verify_email(VERIFICATION_CODE - 1, valid_user()["user_id"])
        assert res != ""

        user = usersdb.get([valid_user()["user_id"]])
        assert user is not None
        assert user["email"] == user["email"], "Should not change email"

        assert self.google_client.has_pending_email(
            valid_user()["user_id"]
        ), "Should not remove pending email"
