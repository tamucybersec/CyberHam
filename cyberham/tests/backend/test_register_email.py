from backend_patcher import BackendPatcher
from cyberham.apis.types import EmailPending
from cyberham.backend import register_email
from cyberham.database.types import User
from cyberham.tests.models import (
    users,
    valid_user,
    no_email_user,
    unregistered_user,
    flagged_user,
    pending_users,
)
from datetime import datetime


class TestRegisterEmail(BackendPatcher):
    def setup_method(self):
        self.initial_users = users
        self.initial_pending = pending_users
        super().setup_method()
        self.now = datetime.now()

    def test_already_registered(self):
        res = register_email(valid_user["user_id"], valid_user["email"], 0)

        assert (
            res == ""
        ), "Should return no status for already registered users not changing their email"
        assert (
            self._has_pending_email(valid_user) == False
        ), "Should not send a verification code to users not changing their email"
        assert self._no_offenses(
            valid_user
        ), "No offense should be created for users not changing their email"

    def test_register_email(self):
        res = register_email(
            unregistered_user["user_id"], unregistered_user["email"], 0
        )

        assert res != ""
        self._assert_valid_pending_email(unregistered_user, unregistered_user["email"])
        assert self._no_offenses(
            unregistered_user
        ), "There should no offenses for one attempt"

    def test_registered_new_email(self):
        email = "new_email@tamu.edu"
        res = register_email(no_email_user["user_id"], email, 0)

        assert res != ""
        self._assert_valid_pending_email(no_email_user, email)
        assert self._no_offenses(
            no_email_user
        ), "There should be no offenses for one attempt"

    def test_register_offense(self):
        prev_pending: EmailPending | None = None

        for i in range(1, 10):
            res = register_email(flagged_user["user_id"], flagged_user["email"], 0)
            assert res != ""
            self._assert_valid_pending_email(flagged_user, flagged_user["email"])

            if i == 0:
                assert self._no_offenses(flagged_user), "There should be no offenses"
            else:
                assert (
                    self._offense_count(flagged_user) == i
                ), "Should have expected offense count"

            if i < 3:
                prev_pending = self.google_client.get_pending_email(
                    flagged_user["user_id"]
                )
            elif i > 3:
                assert prev_pending is not None
                assert (
                    prev_pending["code"]
                    == self.google_client.get_pending_email(flagged_user["user_id"])[
                        "code"
                    ]
                ), "Should retain the same pending email"

    def _assert_valid_pending_email(self, user: User, email: str):
        after = datetime.now()

        assert self._has_pending_email(user), "User should have a pending email"
        pending: EmailPending = self.google_client.get_pending_email(user["user_id"])

        assert (
            pending["user_id"] == user["user_id"]
        ), "Pending email's user_id should match"
        assert pending["email"] == email, "Pending email's email should match"
        assert 1_000 <= pending["code"] < 10_000, "Pending email's code should be rng"
        assert (
            self.now <= pending["time"] <= after
        ), "Pending email's timestamp should be now"

    def _has_pending_email(self, user: User):
        return self.google_client.has_pending_email(user["user_id"])

    def _no_offenses(self, user: User) -> bool:
        flagged = self.flaggeddb.get([user["user_id"]])
        return flagged == None

    def _offense_count(self, user: User) -> int:
        flagged = self.flaggeddb.get([user["user_id"]])

        if flagged is None:
            raise Exception(f"No offenses for user {user['user_id']}")
        return flagged["offences"]
