import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


message = Mail(
    from_email='ceo@mlground.com',
    to_emails='snbharadwaj.r19@gmail.com',
    subject='SendGrid Python Test ✅',
    html_content='<strong>Hello from Python — works perfectly!</strong>'
)
SENDGRID_API_KEY='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'
try:
    api_key = SENDGRID_API_KEY
    if not api_key:
        raise ValueError("Missing SENDGRID_API_KEY. Export it first.")
    sg = SendGridAPIClient(api_key)
    response = sg.send(message)
    print(f"✅ Status Code: {response.status_code}")
    if response.status_code == 202:
        print("📨 Email queued successfully!")
    else:
        print(f"Response: {response.body}")
except Exception as e:
    print(f"❌ Error: {e}")
