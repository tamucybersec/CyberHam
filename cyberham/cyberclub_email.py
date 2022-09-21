import os.path
import base64
import mimetypes

from dataclasses import dataclass
from datetime import datetime

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

from cyberham.config import gmail_token, client_secret

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://mail.google.com/"]


@dataclass
class EmailPending:
    user_id: int
    email: str
    code: int
    time: datetime


class CyberClub:
    def __init__(self):
        """Shows basic usage of the Gmail API.
        Lists the user's Gmail labels.
        """
        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(gmail_token):
            self.creds = Credentials.from_authorized_user_file(gmail_token, SCOPES)
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
            gmail_token.write_text(self.creds.to_json())

    def send_email(self, address: str, code: str):
        try:
            # create gmail api client
            service = build("gmail", "v1", credentials=self.creds)

            message = EmailMessage()

            message.set_content(
                "Welcome to Texas A&M Cybersecurity Club!\n\n"
                
                "-----------------------------------------------------------\n"
                f"CODE: [{code}]\n"
                "-----------------------------------------------------------"
                
                "\n\nContact:\n"
                "discord: Bit#0821"
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
        except HttpError as error:
            print(f"An error occurred: {error}")
            send_message = None
        return send_message