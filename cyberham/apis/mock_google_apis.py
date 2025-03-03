from cyberham.apis.types import EmailPending
from datetime import datetime, timezone


class MockGoogleClient:
    pending_emails: dict[int, EmailPending] = {}

    def send_email(self, address: str, code: str, org: str):
        # unnecessary for mock implementation
        pass

    def get_events(self):
        # TODO when testing __main__.py
        pass

    def has_pending_email(self, user_id: int):
        return user_id in self.pending_emails

    def get_pending_email(self, user_id: int):
        return self.pending_emails[user_id]

    def set_pending_email(self, user_id: int, verification: EmailPending):
        self.pending_emails[user_id] = verification

    def remove_pending_email(self, user_id: int):
        del self.pending_emails[user_id]

    def wipe_pending_email(self, user_id: int):
        """
        Wipe randomly generated attributes of a pending email for testing purposes.
        """

        prev = self.get_pending_email(user_id)
        self.pending_emails[user_id] = EmailPending(
            user_id=prev["user_id"],
            email=prev["email"],
            code=-1,
            time=datetime.fromtimestamp(0, tz=timezone.utc),
        )
