"""
notification_manager.py

This module defines the NotificationManager class, which handles sending flight deal notifications
via:
- SMS or WhatsApp (using the Twilio API).
- Email (using SMTP, e.g., Gmail).

Key responsibilities:
- Format and send SMS/WhatsApp notifications with flight deal details.
- Fetch customer emails from Sheety (via DataManager) and send Email notifications.

Environment Variables required in `.env`:
- TWILIO_ACCOUNT_SID: Twilio SID from dashboard
- TWILIO_AUTH_TOKEN: Twilio auth token
- TWILIO_FROM: Sender number (e.g., +123456789 or whatsapp:+123456789)
- TWILIO_TO: Receiver number (same format as TWILIO_FROM)
- EMAIL_ADDRESS: Sender Gmail address
- EMAIL_PASSWORD: Gmail app password
- SMTP_SERVER: SMTP server address (e.g., smtp.gmail.com)
- SMTP_PORT: SMTP server port (e.g., 587)

Usage:
    from notification_manager import NotificationManager
    nm = NotificationManager()
    nm.send_sms(flight_data)
    nm.send_emails(flight_data)   # auto-sends to all Sheety users

Dependencies:
- twilio
- python-dotenv
"""

import os
import smtplib
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from dotenv import load_dotenv
from flight_data import FlightData
from data_manager import DataManager  # ✅ import DataManager

# Load environment variables from .env file
load_dotenv()


class NotificationManager:
    """
    A class responsible for sending flight deal notifications via:
    - Twilio (SMS/WhatsApp).
    - Email (SMTP).

    Attributes:
        client (Client): Twilio client authenticated with SID + token.
        from_number (str): Sender phone number for Twilio.
        to_number (str): Receiver phone number for Twilio.
        email_address (str): Email account used to send notifications.
        email_password (str): App password for email account.
        smtp_server (str): SMTP server address.
        smtp_port (int): SMTP server port number.

    Methods:
        __init__():
            Initialize Twilio, Email, and Sheety (DataManager).

        send_sms(flight_data: FlightData) -> None:
            Send a formatted flight deal notification via SMS or WhatsApp.

        send_emails(flight_data: FlightData) -> None:
            Fetch user emails from Sheety and send notifications to all of them.
    """

    def __init__(self) -> None:
        """Initialize Twilio, Email, and Sheety credentials from environment variables."""
        # Twilio
        self.client: Client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.from_number: str = os.getenv("TWILIO_FROM", "")
        self.to_number: str = os.getenv("TWILIO_TO", "")

        # Email
        self.email_address: str = os.getenv("EMAIL_ADDRESS", "")
        self.email_password: str = os.getenv("EMAIL_PASSWORD", "")
        self.smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port: int = int(os.getenv("SMTP_PORT", "587"))

        # Data Manager (Sheety)
        self.data_manager: DataManager = DataManager()

    def send_sms(self, flight_data: FlightData) -> None:
        """
        Send a formatted flight deal notification via SMS or WhatsApp.
        """
        try:
            message_body: str = (
                f"✈️ DEAL ALERT:\n{flight_data.as_string()}"
                if hasattr(flight_data, "as_string")
                else (
                    f"✈️ Low price alert! Only {flight_data.price} {getattr(flight_data, 'currency', 'EUR')} "
                    f"to fly from {flight_data.origin_airport} to {flight_data.destination_airport}, "
                    f"from {flight_data.out_date} to {flight_data.return_date}."
                )
            )

            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=self.to_number
            )
            print(f"📤 SMS sent! SID: {message.sid}")

        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")

    def send_emails(self, flight_data: FlightData) -> None:
        """
        Fetch customer emails from Sheety and send flight deal notifications.

        Args:
            flight_data (FlightData): Flight details to include in the email.

        Returns:
            None
        """
        try:
            # --- Get emails from Sheety ---
            users = self.data_manager.get_customer_emails()
            email_list: List[str] = [user["email"] for user in users if user["email"]]

            if not email_list:
                print("⚠️ No emails found in Sheety user list.")
                return

            # --- Format message body ---
            message_body: str = (
                f"✈️ DEAL ALERT:\n\n{flight_data.as_string()}"
                if hasattr(flight_data, "as_string")
                else (
                    f"✈️ Low price alert! Only {flight_data.price} {getattr(flight_data, 'currency', 'EUR')} "
                    f"to fly from {flight_data.origin_airport} to {flight_data.destination_airport}, "
                    f"from {flight_data.out_date} to {flight_data.return_date}."
                )
            )

            # --- Build email ---
            subject: str = "✈️ Flight Deal Alert!"
            msg: MIMEMultipart = MIMEMultipart()
            msg["From"] = self.email_address
            msg["Subject"] = subject
            msg.attach(MIMEText(message_body, "plain", "utf-8"))

            # --- Send email to each Sheety user ---
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as connection:
                connection.starttls()
                connection.login(user=self.email_address, password=self.email_password)

                for recipient in email_list:
                    msg["To"] = recipient
                    connection.sendmail(
                        from_addr=self.email_address,
                        to_addrs=recipient,
                        msg=msg.as_string()
                    )
                    print(f"📧 Email sent to {recipient}")

        except Exception as e:
            print(f"❌ Failed to send emails: {e}")


# ============================
# Optional Test Block
# ============================
if __name__ == "__main__":
    print("\n==============================")
    print("🧪 TEST: Notification Manager")
    print("==============================")

    mock_flight = FlightData(
        price=199.99,
        origin_airport="MAD",
        destination_airport="CDG",
        out_date="2025-11-01",
        return_date="2025-11-10",
        currency="EUR",
        trip_type="round"
    )

    print("\n📄 Flight Data (Formatted):")
    print(mock_flight.as_string())

    notifier: NotificationManager = NotificationManager()

    # --- Test SMS ---
    print("\n📤 Sending test SMS...")
    notifier.send_sms(mock_flight)

    # --- Test Email (to all Sheety users) ---
    print("\n📧 Sending test Emails to all Sheety users...")
    notifier.send_emails(mock_flight)

    print("\n✅ Done.")
