import smtplib
import os
from email.message import EmailMessage

# Configuration
GMAIL_USER = os.getenv("GMAIL_USER")      # Your email address
GMAIL_PASS = os.getenv("GMAIL_APP_PASS")  # Your App Password
RECIPIENT  = os.getenv("RECIPIENT")       # Recipient's email address

def send_success_email(summary):
    """Sends a notification on successful execution."""
    msg = EmailMessage()
    msg['Subject'] = "✅ THM Automation: Success"
    msg['From'] = GMAIL_USER
    msg['To'] = RECIPIENT
    msg.set_content(f"The TryHackMe automation completed successfully.\n\nSummary:\n{summary}")
    
    _dispatch_email(msg)

def send_failure_email(error_message):
    """Sends a notification on execution failure."""
    msg = EmailMessage()
    msg['Subject'] = "❌ THM Automation: FAILED"
    msg['From'] = GMAIL_USER
    msg['To'] = RECIPIENT
    msg.set_content(f"The TryHackMe automation encountered an error:\n\n{error_message}")
    
    _dispatch_email(msg)

def _dispatch_email(msg):
    """Helper function to handle SMTP connection."""
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        print("[+] Email notification sent successfully.")
    except Exception as e:
        print(f"[!] Critical failure sending email: {e}")

# Example Usage:
# if success:
#     send_success_email("All rooms synced successfully.")
# else:
#     send_failure_email("Connection timeout during Selenium headless start.")