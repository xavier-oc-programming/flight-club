# test.py
"""
Test script to troubleshoot email sending via Gmail SMTP.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load .env
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def send_test_email():
    try:
        # Build test message
        subject = "✅ Test Email from Flight Deals Project"
        body = "Hello!\n\nThis is a test email to check if SMTP credentials work.\n\n- Flight Deals Bot"

        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = EMAIL_ADDRESS  # Send to yourself first
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Open connection
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as connection:
            print("🔌 Connecting to SMTP server...")
            connection.starttls()
            print("🔐 Logging in...")
            connection.login(user=EMAIL_ADDRESS, password=EMAIL_PASSWORD)

            print(f"📤 Sending email to {EMAIL_ADDRESS} ...")
            connection.sendmail(
                from_addr=EMAIL_ADDRESS,
                to_addrs=EMAIL_ADDRESS,
                msg=msg.as_string()
            )

        print("✅ Test email sent successfully!")

    except Exception as e:
        print(f"❌ Error while sending test email: {e}")


if __name__ == "__main__":
    send_test_email()
