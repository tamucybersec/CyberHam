from datetime import datetime
from unittest.mock import patch

import pytest
from backend_patcher import BackendPatcher

from cyberham.backend.register import register
from cyberham.database.typeddb import registerdb, usersdb, verifydb
from cyberham.tests.models import valid_user
from cyberham.types import Register


class TestRegister(BackendPatcher):
    @pytest.mark.parametrize(
        "stored_verified, email_changed, submitted_verified, expected_verified",
        [
            (None, False, 1, 0),  # new users cannot verify themselves
            (0, False, 1, 0),  # existing unverified users cannot verify themselves
            (1, False, 0, 1),  # unchanged emails retain stored verification
            (1, True, 1, 0),  # changed emails require verification
        ],
    )
    def test_register_verification(
        self,
        stored_verified: int | None,
        email_changed: bool,
        submitted_verified: int,
        expected_verified: int,
    ):
        user = valid_user()
        if stored_verified is not None:
            user["verified"] = stored_verified
            usersdb.create(user)

        user["verified"] = submitted_verified
        if email_changed:
            user["email"] = "new@tamu.edu"
        registerdb.create(
            Register(
                ticket="test-ticket",
                user_id=user["user_id"],
                time=datetime.now().isoformat(),
            )
        )

        with patch.object(self.google_client, "send_email") as send_email:
            _, err = register("test-ticket", user)

        assert err is None
        saved = usersdb.get((user["user_id"],))
        assert saved is not None
        assert saved["verified"] == expected_verified
        pending = verifydb.get((user["user_id"],))
        if expected_verified:
            assert pending is None
            send_email.assert_not_called()
        else:
            assert pending is not None
            send_email.assert_called_once_with(
                user["email"], str(pending["code"]), "Texas A&M Cybersecurity Club"
            )
