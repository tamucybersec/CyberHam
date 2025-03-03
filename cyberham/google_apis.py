import logging
import os.path
import base64

# import mimetypes


from dataclasses import dataclass
from typing import TypedDict, cast
from datetime import datetime, timedelta, time
from googleapiclient._apis.gmail.v1.schemas import Message
from pytz import timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email.message import EmailMessage

# from email.mime.audio import MIMEAudio
# from email.mime.base import MIMEBase
# from email.mime.image import MIMEImage
# from email.mime.text import MIMEText

from cyberham import google_token, client_secret

# If modifying these scopes, delete the file token.json.
SCOPES: list[str] = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar.readonly",
]
logger = logging.getLogger(__name__)


@dataclass
class EmailPending:
    user_id: int
    email: str
    code: int
    time: datetime


class CalendarEvent(TypedDict):
    id: str
    name: str
    start: datetime
    end: datetime
    location: str


class GoogleClient:
    creds: Credentials | None = None

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
        send_message: Message | None = None

        try:
            # create gmail api client
            service = build("gmail", "v1", credentials=self.creds)

            message = EmailMessage()

            message.set_content(
                f"Welcome to {org}!\n\n"
                "-----------------------------------------------------------\n"
                f"CODE: [{code}]\n"
                "-----------------------------------------------------------"
                "\n\nContact:\n"
                "discord: bit.py"
            )

            message["To"] = address
            message["From"] = "CyberHam<tamucybersec@gmail.com>"
            message["Subject"] = "CyberHam verification code"

            # encoded message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            # pylint: disable=E1101
            send_message = (
                service.users()
                .messages()
                .send(userId="me", body=cast(Message, create_message))
                .execute()
            )

            if "id" in send_message:
                logger.info(f'Message Id: {send_message["id"]}')
                logger.info(f"[{code}] -> {address}")
            else:
                logger.info(f"Error: sent message missing id")
                logger.info(f"[{code}] -> {address}")

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            send_message = None

        return send_message

    def get_events(self):
        result: list[CalendarEvent] | None = None

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
                logger.info("No upcoming events found.")
                return

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
                start = event["start"].get("dateTime", event["start"].get("date"))
                start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")  # type: ignore
                end = event["end"].get("dateTime", event["end"].get("date"))
                end = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")  # type: ignore
                summary = event["summary"]
                location = event["location"] if ("location" in event) else "TBD"

                result.append(
                    CalendarEvent(
                        id=event_id,
                        name=summary,
                        start=start,
                        end=end,
                        location=location,
                    )
                )

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            result = None
        except TypeError as error:
            logger.error(f"An error occurred: {error}")
            result = None

        return result
