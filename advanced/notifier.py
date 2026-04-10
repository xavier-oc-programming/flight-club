import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


class Notifier:
    """Handles SMS (Twilio) and email (SMTP) notifications for flight deal alerts."""

    def __init__(self, email_subject: str, smtp_server: str, smtp_port: int) -> None:
        self._twilio_client = Client(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )
        self._from_number: str = os.environ["TWILIO_FROM"]
        self._to_number: str = os.environ["TWILIO_TO"]

        self._email_address: str = os.environ["EMAIL_ADDRESS"]
        self._email_password: str = os.environ["EMAIL_PASSWORD"]
        self._smtp_server = smtp_server
        self._smtp_port = smtp_port
        self._email_subject = email_subject

    def send_sms(self, message_body: str) -> None:
        """Send an SMS via Twilio. Raises on failure."""
        message = self._twilio_client.messages.create(
            body=message_body,
            from_=self._from_number,
            to=self._to_number,
        )
        print(f"SMS sent. SID: {message.sid}")

    def send_emails(self, message_body: str, recipients: List[str]) -> None:
        """Send the message body to each address in recipients via Gmail SMTP. Raises on failure."""
        if not recipients:
            print("No recipients — skipping email.")
            return

        with smtplib.SMTP(self._smtp_server, self._smtp_port) as connection:
            connection.starttls()
            connection.login(user=self._email_address, password=self._email_password)

            for recipient in recipients:
                msg = MIMEMultipart()
                msg["From"] = self._email_address
                msg["To"] = recipient
                msg["Subject"] = self._email_subject
                msg.attach(MIMEText(message_body, "plain", "utf-8"))
                connection.sendmail(
                    from_addr=self._email_address,
                    to_addrs=recipient,
                    msg=msg.as_string(),
                )
                print(f"Email sent to {recipient}")
