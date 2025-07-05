from backend_patcher import BackendPatcher
from cyberham.backend.register import register_email
from cyberham.types import User, Verify
from cyberham.tests.models import (
    users,
    valid_user,
    no_email_user,
    unregistered_user,
    flagged_user,
    pending_verifies,
)
from datetime import datetime
from cyberham.database.typeddb import flaggeddb, verifydb


class TestRegisterEmail(BackendPatcher):
    def setup_method(self):
        self.initial_users = users()
        self.initial_verify = pending_verifies()
        super().setup_method()
        self.now = datetime.now()

    def test_already_registered(self):
        res, err = register_email(valid_user()["user_id"], valid_user()["email"])

        assert err is None
        assert (
            res == ""
        ), "Should return no status for already registered users not changing their email"
        assert (
            self._has_pending_verify(valid_user()) == False
        ), "Should not send a verification code to users not changing their email"
        assert self._no_offenses(
            valid_user()
        ), "No offense should be created for users not changing their email"

    def test_register_email(self):
        res = register_email(
            unregistered_user()["user_id"], unregistered_user()["email"]
        )

        assert res != ""
        self._assert_valid_pending_email(
            unregistered_user(), unregistered_user()["email"]
        )
        assert self._no_offenses(
            unregistered_user()
        ), "There should no offenses for one attempt"

    def test_registered_new_email(self):
        email = "new_email@tamu.edu"
        res = register_email(no_email_user()["user_id"], email)

        assert res != ""
        self._assert_valid_pending_email(no_email_user(), email)
        assert self._no_offenses(
            no_email_user()
        ), "There should be no offenses for one attempt"

    def test_register_offense(self):
        prev_pending: Verify | None = None

        for i in range(1, 10):
            res = register_email(
                flagged_user()["user_id"], flagged_user()["email"] + "new"
            )
            assert res != ""
            self._assert_valid_pending_email(
                flagged_user(), flagged_user()["email"] + "new"
            )

            if i == 0:
                assert self._no_offenses(flagged_user()), "There should be no offenses"
            else:
                assert (
                    self._offense_count(flagged_user()) == i
                ), "Should have expected offense count"

            if i < 3:
                prev_pending = verifydb.get((flagged_user()["user_id"],))
            elif i > 3:
                assert prev_pending is not None
                pending = verifydb.get((flagged_user()["user_id"],))
                assert pending is not None
                assert (
                    prev_pending["code"] == pending["code"]
                ), "Should retain the same pending email"

    def _assert_valid_pending_email(self, user: User, email: str):
        assert self._has_pending_verify(user), "User should have a pending email"
        pending = verifydb.get((user["user_id"],))

        assert pending is not None
        assert (
            pending["user_id"] == user["user_id"]
        ), "Pending email's user_id should match"
        assert 1_000 <= pending["code"] < 10_000, "Pending email's code should be rng"

    def _has_pending_verify(self, user: User):
        return verifydb.get((user["user_id"],)) is not None

    def _no_offenses(self, user: User) -> bool:
        flagged = flaggeddb.get((user["user_id"],))
        return flagged == None

    def _offense_count(self, user: User) -> int:
        flagged = flaggeddb.get((user["user_id"],))

        if flagged is None:
            raise Exception(f"No offenses for user {user['user_id']}")
        return flagged["offenses"]
