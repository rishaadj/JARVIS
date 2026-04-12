import smtplib
import os
from email.message import EmailMessage

def execute(params):
    to_email = params.get("to")
    subject = params.get("subject", "Message from JARVIS")
    body = params.get("body")
    
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    
    if not sender_email or not sender_password:
        return "Sir, credentials (EMAIL_USER/PASS) are missing from the environment."

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return f"Sir, the email to {to_email} has been dispatched."
    except Exception as e:
        return f"Sir, the mail server rejected the request: {str(e)}"