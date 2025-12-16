import smtplib
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.config import get_settings
import structlog

logger = structlog.get_logger()
settings = get_settings()


class EmailIntegration:
    """Email sending and receiving integration"""
    
    def __init__(self):
        self.smtp_server = settings.EMAIL_SMTP_SERVER
        self.smtp_port = settings.EMAIL_SMTP_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email via SMTP"""
        if not self.username or not self.password:
            logger.warning("Email not configured, skipping send")
            return False
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = self.username
            message['To'] = to
            message['Subject'] = subject
            
            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            if html_body:
                message.attach(MIMEText(html_body, 'html'))
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                start_tls=True
            )
            
            logger.info("Email sent", to=to, subject=subject)
            return True
            
        except Exception as e:
            logger.error("Failed to send email", to=to, error=str(e))
            return False
    
    async def send_password_reset_email(self, user_email: str, temp_password: str) -> bool:
        """Send password reset notification"""
        subject = "Your Password Has Been Reset"
        
        body = f"""
Hello,

Your password has been reset as requested.

Temporary Password: {temp_password}

You will be required to change this password on your next login.

If you did not request this password reset, please contact IT support immediately.

Best regards,
IT Support Automation System
"""
        
        html_body = f"""
<html>
<body>
    <h2>Password Reset Notification</h2>
    <p>Hello,</p>
    <p>Your password has been reset as requested.</p>
    <p><strong>Temporary Password:</strong> <code>{temp_password}</code></p>
    <p>You will be required to change this password on your next login.</p>
    <p style="color: red;">If you did not request this password reset, please contact IT support immediately.</p>
    <br>
    <p>Best regards,<br>IT Support Automation System</p>
</body>
</html>
"""
        
        return await self.send_email(user_email, subject, body, html_body)
    
    async def send_account_unlock_email(self, user_email: str) -> bool:
        """Send account unlock notification"""
        subject = "Your Account Has Been Unlocked"
        
        body = f"""
Hello,

Your account has been unlocked and you can now log in.

If you continue to experience issues, please contact IT support.

Best regards,
IT Support Automation System
"""
        
        html_body = f"""
<html>
<body>
    <h2>Account Unlocked</h2>
    <p>Hello,</p>
    <p>Your account has been unlocked and you can now log in.</p>
    <p>If you continue to experience issues, please contact IT support.</p>
    <br>
    <p>Best regards,<br>IT Support Automation System</p>
</body>
</html>
"""
        
        return await self.send_email(user_email, subject, body, html_body)
    
    async def send_ticket_resolved_email(
        self,
        user_email: str,
        ticket_number: str,
        resolution: str
    ) -> bool:
        """Send ticket resolution notification"""
        subject = f"Ticket {ticket_number} - Resolved"
        
        body = f"""
Hello,

Your IT support ticket {ticket_number} has been automatically resolved.

Resolution:
{resolution}

If you continue to experience issues, please reply to this email or create a new ticket.

Best regards,
IT Support Automation System
"""
        
        html_body = f"""
<html>
<body>
    <h2>Ticket Resolved: {ticket_number}</h2>
    <p>Hello,</p>
    <p>Your IT support ticket has been automatically resolved.</p>
    <div style="background-color: #f0f0f0; padding: 10px; margin: 10px 0;">
        <strong>Resolution:</strong>
        <p>{resolution}</p>
    </div>
    <p>If you continue to experience issues, please reply to this email or create a new ticket.</p>
    <br>
    <p>Best regards,<br>IT Support Automation System</p>
</body>
</html>
"""
        
        return await self.send_email(user_email, subject, body, html_body)


# Global instance
email_integration = EmailIntegration()
