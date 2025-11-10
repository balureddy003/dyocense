"""
Email notification channel using SendGrid/SMTP
"""
import logging
from datetime import datetime
from typing import Any

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..models import (
    EmailNotificationData,
    Notification,
    NotificationChannel as ChannelEnum,
    NotificationDelivery,
)
from .base import NotificationChannel

logger = logging.getLogger(__name__)


class EmailChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.smtp_host = config.get('smtp_host', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_user = config.get('smtp_user')
        self.smtp_password = config.get('smtp_password')
        self.use_tls = config.get('use_tls', True)
        self.from_email = config.get('from_email', 'coach@dyocense.com')
    
    def validate_config(self) -> bool:
        """Validate email configuration"""
        required = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password']
        return all(self.config.get(k) for k in required)
    
    async def send(self, notification: Notification) -> NotificationDelivery:
        """Send email notification"""
        delivery = NotificationDelivery(
            id=f"{notification.id}_email_{datetime.utcnow().timestamp()}",
            notification_id=notification.id,
            channel=ChannelEnum.EMAIL,
            status="pending",
        )
        
        try:
            # Get email-specific data or generate from notification
            email_data = notification.data.get('email', {})
            subject = email_data.get('subject', notification.title)
            body_html = email_data.get('body_html', self._generate_html(notification))
            body_text = email_data.get('body_text', notification.message)
            to_email = notification.data.get('recipient_email')
            
            if not to_email:
                raise ValueError("Recipient email not provided")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Attach text and HTML parts
            part1 = MIMEText(body_text, 'plain')
            part2 = MIMEText(body_html, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send via SMTP
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=self.use_tls,
            )
            
            delivery.status = "sent"
            delivery.sent_at = datetime.utcnow()
            logger.info(f"Email sent to {to_email}: {subject}")
            
        except Exception as e:
            delivery.status = "failed"
            delivery.error = str(e)
            logger.error(f"Failed to send email: {e}")
        
        return delivery
    
    def _generate_html(self, notification: Notification) -> str:
        """Generate HTML email template"""
        # Business fitness coach themed email template
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{notification.title}</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8f9fa;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8f9fa; padding: 40px 20px;">
                <tr>
                    <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <!-- Header -->
                            <tr>
                                <td style="padding: 32px 32px 24px; text-align: center; border-bottom: 1px solid #e9ecef;">
                                    <h1 style="margin: 0; font-size: 24px; font-weight: 600; color: #212529;">
                                        🎯 {notification.title}
                                    </h1>
                                </td>
                            </tr>
                            
                            <!-- Body -->
                            <tr>
                                <td style="padding: 32px; color: #495057; font-size: 16px; line-height: 1.6;">
                                    {notification.message}
                                </td>
                            </tr>
                            
                            <!-- CTA Button (if action provided) -->
                            {self._get_cta_html(notification)}
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 24px 32px; text-align: center; border-top: 1px solid #e9ecef; color: #6c757d; font-size: 14px;">
                                    <p style="margin: 0 0 8px;">Keep up the great work! 💪</p>
                                    <p style="margin: 0; font-size: 12px;">
                                        <a href="{notification.data.get('preferences_url', '#')}" style="color: #6c757d; text-decoration: underline;">
                                            Notification preferences
                                        </a>
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    def _get_cta_html(self, notification: Notification) -> str:
        """Generate CTA button HTML if action URL provided"""
        action_url = notification.data.get('action_url')
        action_text = notification.data.get('action_text', 'View Dashboard')
        
        if not action_url:
            return ""
        
        return f"""
        <tr>
            <td style="padding: 0 32px 32px; text-align: center;">
                <a href="{action_url}" style="display: inline-block; padding: 12px 32px; background-color: #0ea5e9; color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 16px;">
                    {action_text}
                </a>
            </td>
        </tr>
        """
