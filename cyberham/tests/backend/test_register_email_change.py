from datetime import datetime
from uuid import uuid4

from backend_patcher import BackendPatcher

from cyberham.backend.register import register, verify_email
from cyberham.database.typeddb import registerdb, usersdb, verifydb
from cyberham.tests.models import unregistered_user
from cyberham.types import MaybeError, Register, User

RESENDS_BEFORE_BLOCK = 3


class TestRegisterEmailChange(BackendPatcher):
    def setup_method(self):
        super().setup_method()
        self.user_id = unregistered_user()["user_id"]
        self.email = unregistered_user()["email"]

    def test_blocked_email_change_voids_previous_code(self):
        new_email = "someone_else@tamu.edu"
        previous_code = self._register_until_last_resend()

        err = self._register(new_email)

        assert err is not None, "Should block the resend"
        assert verify_email(previous_code, self.user_id) == "This code is not correct!"
        user = self._user()
        assert user["email"] == new_email
        assert not user["verified"], (
            "A code sent to the previous email should not verify the new one"
        )

    def test_blocked_resend_keeps_code_for_same_email(self):
        previous_code = self._register_until_last_resend()

        err = self._register(self.email)

        assert err is not None, "Should block the resend"
        assert "verified!" in verify_email(previous_code, self.user_id)
        user = self._user()
        assert user["email"] == self.email
        assert user["verified"]

    def test_email_change_sends_new_code(self):
        new_email = "someone_else@tamu.edu"
        assert self._register(self.email) is None

        assert self._register(new_email) is None

        assert "verified!" in verify_email(self._pending_code(), self.user_id)
        assert self._user()["email"] == new_email

    def _register_until_last_resend(self) -> int:
        for _ in range(RESENDS_BEFORE_BLOCK):
            assert self._register(self.email) is None
        return self._pending_code()

    def _register(self, email: str) -> MaybeError:
        ticket = str(uuid4())
        registerdb.create(
            Register(
                user_id=self.user_id, ticket=ticket, time=datetime.now().isoformat()
            )
        )
        user = unregistered_user()
        user["email"] = email
        user["verified"] = 0
        _, err = register(ticket, user)
        return err

    def _pending_code(self) -> int:
        pending = verifydb.get((self.user_id,))
        assert pending is not None
        return pending["code"]

    def _user(self) -> User:
        user = usersdb.get((self.user_id,))
        assert user is not None
        return user
