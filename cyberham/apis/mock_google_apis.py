from cyberham.apis.google_apis import GoogleClientProtocol
from cyberham.apis.types import EmailPending
from copy import deepcopy


class MockGoogleClient(GoogleClientProtocol):
    pending_emails: dict[int, EmailPending] = {}

    def __init__(self, initial_pending: list[EmailPending]):
        self.pending_emails.clear()
        for pending in initial_pending:
            self.pending_emails[pending["user_id"]] = deepcopy(pending)

    def send_email(self, address: str, code: str, org: str):
        # unnecessary for mock implementation
        pass

    def get_events(self):
        # implement when testing discord bot commands
        pass

    def has_pending_email(self, user_id: int):
        return user_id in self.pending_emails

    def get_pending_email(self, user_id: int):
        return deepcopy(self.pending_emails[user_id])

    def set_pending_email(self, user_id: int, verification: EmailPending):
        self.pending_emails[user_id] = deepcopy(verification)

    def remove_pending_email(self, user_id: int):
        del self.pending_emails[user_id]
