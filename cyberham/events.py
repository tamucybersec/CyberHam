import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import datetime,timedelta

from cyberham import calendar_token, calendar_client_secret

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

class EventCalendar:
    def __init__(self):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(calendar_token):
            self.creds = Credentials.from_authorized_user_file(calendar_token, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    calendar_client_secret, SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            calendar_token.write_text(self.creds.to_json())

    def get_events(self):
        try:
            service = build("calendar", "v3", credentials=self.creds)
        
            # Call the Calendar API
            week = timedelta(days=7)
            now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
            later = (datetime.utcnow()+week).isoformat() + "Z"
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
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
                # print(event)
                id = event["id"]
                start = event["start"].get("dateTime", event["start"].get("date"))
                start = datetime.strptime(start,"%Y-%m-%dT%H:%M:%S%z")
                end = event["end"].get("dateTime", event["end"].get("date"))
                end = datetime.strptime(end,"%Y-%m-%dT%H:%M:%S%z")
                summary = event["summary"]
                result.append({"id":id,"name":summary,"start":start,"end":end})
                
        except HttpError as error:
            print(f"An error occurred: {error}")
            result = None
        return result