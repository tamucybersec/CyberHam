from cyberham.apis.google_apis import GoogleClientProtocol
from cyberham.types import CalendarEvent, MaybeError


class MockGoogleClient(GoogleClientProtocol):
    def send_email(self, address: str, code: str, org: str):
        # unnecessary for mock implementation
        pass

    def get_events(self) -> tuple[list[CalendarEvent], MaybeError]:
        # implement when testing discord bot commands
        return [], None
