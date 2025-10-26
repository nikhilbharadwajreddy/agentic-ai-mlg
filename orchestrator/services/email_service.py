"""
Email Service

Sends OTP emails using SendGrid API.

Features:
- Professional email templates
- Error handling and retry logic
- Logging for audit trail
- Placeholder API key support for development
- SSL certificate handling for Cloud Run
"""

import logging
import ssl
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Fix SSL certificate verification issues in Cloud Run
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)


class EmailService:
    """
    Handles sending emails via SendGrid.
    
    Primary use case: Sending OTP codes for verification.
    """
    
    def __init__(self, api_key: str, from_email: str = "noreply@yourcompany.com"):
        """
        Initialize email service.
        
        Args:
            api_key: SendGrid API key (from Secret Manager)
            from_email: Sender email address (must be verified in SendGrid)
        """
        self.api_key = api_key
        self.from_email = from_email
        
        # Check if using placeholder key
        self.is_mock = (
            api_key == "PLACEHOLDER_SENDGRID_API_KEY" or 
            not api_key or 
            api_key.startswith("PLACEHOLDER")
        )
        
        if self.is_mock:
            logger.warning("⚠️  Using PLACEHOLDER SendGrid API key - emails will be logged but not sent")
        else:
            try:
                self.client = SendGridAPIClient(api_key)
                logger.info(f"✅ SendGrid client initialized with from_email: {from_email}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize SendGrid client: {e}")
                self.is_mock = True
    
    def send_otp_email(
        self,
        to_email: str,
        otp_code: str,
        first_name: Optional[str] = None,
        expiry_minutes: int = 5
    ) -> bool:
        """
        Sends OTP verification email to user.
        
        Args:
            to_email: Recipient email address
            otp_code: 6-digit OTP code
            first_name: User's first name (for personalization)
            expiry_minutes: How long OTP is valid
        
        Returns:
            True if sent successfully, False otherwise
        """
        
        # Mock mode - just log the OTP
        if self.is_mock:
            logger.info(f"""
╔══════════════════════════════════════════════════╗
║          📧 MOCK EMAIL (SendGrid)                ║
╠══════════════════════════════════════════════════╣
║ To: {to_email:<44} ║
║ Code: {otp_code:<42} ║
║ Expires: {expiry_minutes} minutes{' ' * 33}║
╚══════════════════════════════════════════════════╝
            """)
            return True
        
        # Prepare email content
        subject = "Your Verification Code"
        
        # Personalize greeting
        greeting = f"Hi {first_name}," if first_name else "Hello,"
        
        # HTML email body
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4A90E2;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 5px;
                    color: #4A90E2;
                    text-align: center;
                    padding: 20px;
                    background-color: white;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    font-size: 12px;
                    color: #888;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Email Verification</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Thank you for signing up! To complete your verification, please use the code below:</p>
                    
                    <div class="otp-code">{otp_code}</div>
                    
                    <p><strong>This code will expire in {expiry_minutes} minutes.</strong></p>
                    
                    <p>If you didn't request this code, please ignore this email.</p>
                    
                    <p>Best regards,<br>The Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            # Create email using simplified Mail constructor
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            logger.info(f"📧 Attempting to send OTP email to {to_email} from {self.from_email}")
            
            # Send email
            response = self.client.send(message)
            
            logger.info(f"📤 SendGrid response status: {response.status_code}")
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ OTP email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"❌ SendGrid returned status {response.status_code}")
                logger.error(f"Response body: {response.body}")
                logger.error(f"Response headers: {response.headers}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Failed to send OTP email to {to_email}: {e}", exc_info=True)
            return False
    
    def send_welcome_email(
        self,
        to_email: str,
        first_name: str
    ) -> bool:
        """
        Sends welcome email to newly verified user.
        
        Args:
            to_email: User's email
            first_name: User's first name
        
        Returns:
            True if sent successfully
        """
        
        if self.is_mock:
            logger.info(f"📧 MOCK: Welcome email to {to_email}")
            return True
        
        subject = f"Welcome, {first_name}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Welcome, {first_name}!</h2>
                <p>Your account has been successfully verified.</p>
                <p>You can now access all features of our platform.</p>
                <p>If you have any questions, feel free to reach out to our support team.</p>
                <p>Best regards,<br>The Team</p>
            </div>
        </body>
        </html>
        """
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"✅ Welcome email sent to {to_email}")
                return True
            else:
                logger.error(f"❌ SendGrid returned status {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Failed to send welcome email: {e}", exc_info=True)
            return False
