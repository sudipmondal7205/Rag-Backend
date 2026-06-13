from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.template.otp_mail_template import mail_otp_html_template
import base64


class EmailService():

    def __init__(self):
        self.creds = Credentials(
            token=None,
            refresh_token=settings.GMAIL_REFRESH_TOKEN,
            token_uri=settings.GOOGLE_TOKEN_URL,
            client_id=settings.GMAIL_CLIENT_ID,
            client_secret=settings.GMAIL_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/gmail.send"]
        )


    async def _refresh_token_if_expired(self):

        if self.creds and self.creds.expired and self.creds.refresh_token:
            await self.creds.refresh(Request())



    async def send_otp_email(self, email_to: str, otp_code: str):
        await self._refresh_token_if_expired()

        service = build("gmail", "v1", credentials=self.creds)

        message = MIMEMultipart('alternative')
        message["To"] = email_to
        message["From"] = "me"
        message["Subject"] = f"Your Verification Code: {otp_code}"

        text_fallback = f"Hello, your verification code is: {otp_code}. It expires in 10 minutes."
        html_content = mail_otp_html_template.format(otp_code=otp_code)

        message.attach(MIMEText(text_fallback, 'plain'))
        message.attach(MIMEText(html_content, 'html'))
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        created_message = {"raw": encoded_message}

        try:
            service.users().messages().send(userId='me', body=created_message).execute()
            return True
        except Exception as e:
            return False

        
        

email_service = EmailService()