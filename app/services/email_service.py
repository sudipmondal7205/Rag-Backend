import base64
from app.core.config import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.message import EmailMessage



class EmailService():

    def __init__(self):
        self.creds = Credentials(
            token=None,
            refresh_token=settings.GMAIL_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/gmail.send"]
        )
    

    async def _refresh_token_if_expired(self):

        if self.creds and self.creds.expired and self.creds.refresh_token:
            self.creds.refresh(Request())



    async def send_email(self, email_to: str, content: str, subject: str):
        self._refresh_token_if_expired()

        service = build("gmail", "v1", credentials=self.creds)

        message = EmailMessage()
        message.set_content(content)
        message["To"] = email_to
        message["From"] = settings.GMAIL_SENDER
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        created_message = {"raw": encoded_message}

        try:
            service.users().messages().send(userId='me', body=created_message).execute()
            return True
        except Exception as e:
            print(str(e))
            return False

        
        

email_service = EmailService()