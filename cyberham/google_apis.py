import os.path
import base64
import mimetypes

from dataclasses import dataclass
from datetime import datetime, timedelta, time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email.message import EmailMessage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

from cyberham import google_token, client_secret

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://mail.google.com/", "https://www.googleapis.com/auth/calendar.readonly"]


@dataclass
class EmailPending:
    user_id: int
    email: str
    code: int
    time: datetime


class GoogleClient:
    def __init__(self):
        """Shows basic usage of the Gmail API.
        Lists the user's Gmail labels.
        """
        self.creds = None
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

    def send_email(self, address: str, code: str, org: str, ):
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
                .send(userId="me", body=create_message)
                .execute()
            )

            print(f'Message Id: {send_message["id"]}')
            print(f'[{code}] -> {address}')
        except HttpError as error:
            print(f"An error occurred: {error}")
            send_message = None
        return send_message

    def get_events(self):
        try:
            service = build("calendar", "v3", credentials=self.creds)

            # Call the Calendar API
            now = datetime.utcnow()
            tz_hours = round((now - datetime.now()).seconds / 3600)
            timezone_diff = time(hour=tz_hours)
            days_to_monday = timedelta(days=8 - (now.weekday() + 1) % 7)
            now = now.isoformat() + "Z"  # 'Z' indicates UTC time
            later = datetime.combine(datetime.utcnow().date() + days_to_monday, timezone_diff)
            later = later.isoformat() + "Z"
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
                print("No upcoming events found.")
                return

            # Moves result of the start, end, and name of the events in the next week
            result = []
            for event in events:
                event_id = event["id"]
                start = event["start"].get("dateTime", event["start"].get("date"))
                start = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
                end = event["end"].get("dateTime", event["end"].get("date"))
                end = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")
                summary = event["summary"]
                if "location" in event:
                    location = event["location"]
                else:
                    location = "TBD"
                result.append({"id": event_id, "name": summary, "start": start, "end": end, "location": location})

        except HttpError as error:
            print(f"An error occurred: {error}")
            result = None
        return result
