import logging
import os.path
import base64

from typing import TYPE_CHECKING, Protocol, runtime_checkable, Any

from datetime import datetime, timedelta, time
from pytz import timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.external_account_authorized_user import Credentials as ExCredentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.errors import HttpError
from email.message import EmailMessage

from cyberham import google_token, client_secret
from cyberham.types import (
    Error,
    MaybeError,
    CalendarEvent,
    VALID_CATEGORIES,
)


# force the type checker to populate the structure to prevent type errors
# finicky, to say the least
if TYPE_CHECKING:
    from googleapiclient.discovery import Resource

    _: Resource


# If modifying these scopes, delete the file token.json.
SCOPES: list[str] = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
]
logger = logging.getLogger(__name__)


@runtime_checkable
class GoogleClientProtocol(Protocol):
    def send_email(self, address: str, code: str, org: str) -> Any | None: ...
    def get_events(self) -> tuple[list[CalendarEvent], MaybeError]: ...


class _Client(GoogleClientProtocol):
    creds: Credentials | ExCredentials | None = None

    def __init__(self):
        """Shows basic usage of the Gmail API.
        Lists the user's Gmail labels.
        """

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(google_token):
            self.creds = Credentials.from_authorized_user_file(google_token, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret,
                    SCOPES,
                )
                self.creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            google_token.write_text(self.creds.to_json())

    def send_email(self, address: str, code: str, org: str):
        try:
            # create gmail api client
            service = build("gmail", "v1", credentials=self.creds)

            message = EmailMessage()

            message.set_content(
                f"Welcome to {org}!\n\n"
                "-----------------------------------------------------------\n"
                f"CODE: [{code}]\n"
                "-----------------------------------------------------------\n\n"
                "Please continue to use /verify in the same place you registered to verify this email.\n\n"
                "If you did not request this code, you can safely ignore this email.\n"
                "For any further questions or information, feel free to reply to this email."
            )

            message["To"] = address
            message["From"] = "CyberHam<tamucybersec@gmail.com>"
            message["Subject"] = "CyberHam Verification Code"

            # encoded message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            # pylint: disable=E1101
            send_message = (
                service.users()
                .messages()
                .send(
                    userId="me",
                    body=create_message,  # type: ignore
                )
                .execute()
            )

            if "id" in send_message:
                print(f'Message Id: {send_message["id"]}')
                print(f"[{code}] -> {address}")
            else:
                print(f"Error: sent message missing id")
                print(f"[{code}] -> {address}")

        except HttpError as error:
            print(f"An error occurred in GoogleClient/send_email: {error}")
            return None

        return send_message

    def get_events(self) -> tuple[list[CalendarEvent], MaybeError]:
        result: list[CalendarEvent] = []

        try:
            service = build("calendar", "v3", credentials=self.creds)

            # Call the Calendar API
            cst_tz = timezone("America/Chicago")
            now = datetime.now(cst_tz)
            days_until_sunday = 6 - now.weekday() if now.weekday() < 6 else 7
            later = now + timedelta(days=days_until_sunday)
            midnight = time(23, 59, 59)
            later = datetime.combine(later, midnight)

            # Adjust the timezone
            later = cst_tz.localize(later)
            now = now.isoformat()
            later = later.isoformat()
            logger.info(f"{now=}")
            logger.info(f"{later=}")

            events_result = (
                service.events()
                .list(
                    calendarId="tamucybersec@gmail.com",
                    timeMin=now,
                    timeMax=later,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                return [], None

            # Moves result of the start, end, and name of the events in the next week
            result = []
            for event in events:
                if not "id" in event:
                    raise TypeError("ID not found for event")
                elif not "start" in event:
                    raise TypeError(f"Start time not found for event {id}")
                elif not "end" in event:
                    raise TypeError(f"End time not found for event {id}")
                elif not "summary" in event:
                    raise TypeError(f"Summary not found for event {id}")

                event_id = event["id"]
                start = str(event["start"].get("dateTime", event["start"].get("date")))
                start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
                end = str(event["end"].get("dateTime", event["end"].get("date")))
                end = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
                name = event["summary"]
                location = event["location"] if ("location" in event) else "TBD"
                category = event["description"] if ("description" in event) else "NONE"

                if not (category in VALID_CATEGORIES):
                    return [], Error(
                        f"Event '{name}' does not have a valid category ({category}). Valid categories: {VALID_CATEGORIES}. Assign the category using the event description."
                    )

                result.append(
                    CalendarEvent(
                        id=event_id,
                        name=name,
                        start=start,
                        end=end,
                        location=location,
                        category=category,
                    )
                )

        except HttpError as error:
            return [], Error(str(error))
        except TypeError as error:
            return [], Error(str(error))

        return result, None


# wrapper Google class to make testing easy
class Google:
    client: GoogleClientProtocol

    def __init__(self):
        self.client = _Client()


google = Google()
