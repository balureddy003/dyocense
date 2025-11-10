"""
Microsoft Teams notification channel using webhooks
"""
import logging
from datetime import datetime
from typing import Any

import aiohttp

from ..models import (
    Notification,
    NotificationChannel as ChannelEnum,
    NotificationDelivery,
)
from .base import NotificationChannel

logger = logging.getLogger(__name__)


class TeamsChannel(NotificationChannel):
    """Microsoft Teams notification channel via webhooks"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.default_webhook_url = config.get('webhook_url')
        self.theme_color = config.get('theme_color', '0078D4')
    
    def validate_config(self) -> bool:
        """Validate Teams configuration"""
        return bool(self.default_webhook_url)
    
    async def send(self, notification: Notification) -> NotificationDelivery:
        """Send Teams notification"""
        delivery = NotificationDelivery(
            id=f"{notification.id or 'notification'}_teams_{datetime.utcnow().timestamp()}",
            notification_id=notification.id or "",
            channel=ChannelEnum.TEAMS,
            status="pending",
        )
        
        try:
            # Get Teams-specific data
            teams_data = notification.data.get('teams', {})
            webhook_url = teams_data.get('webhook_url', self.default_webhook_url)
            
            if not webhook_url:
                raise ValueError("Teams webhook URL not provided")
            
            # Format message
            payload = self._format_teams_message(notification, teams_data)
            
            # Send to Teams
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        delivery.status = "sent"
                        delivery.sent_at = datetime.utcnow()
                        logger.info(f"Teams notification sent: {notification.title}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Teams API error: {response.status} - {error_text}")
        
        except Exception as e:
            delivery.status = "failed"
            delivery.error = str(e)
            logger.error(f"Failed to send Teams notification: {e}")
        
        return delivery
    
    def _format_teams_message(self, notification: Notification, teams_data: dict) -> dict:
        """Format notification as Teams adaptive card"""
        sections = teams_data.get('sections', [])
        
        if not sections:
            # Generate default sections
            sections = [
                {
                    "activityTitle": notification.title,
                    "activitySubtitle": f"Business Fitness Update • {notification.type.replace('_', ' ').title()}",
                    "activityImage": self._get_activity_image(notification.type),
                    "text": notification.message,
                    "markdown": True
                }
            ]
        
        # Add action button if provided
        potential_action = []
        action_url = notification.data.get('action_url')
        if action_url:
            potential_action.append({
                "@type": "OpenUri",
                "name": notification.data.get('action_text', 'View Dashboard'),
                "targets": [
                    {
                        "os": "default",
                        "uri": action_url
                    }
                ]
            })
        
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": teams_data.get('theme_color', self.theme_color),
            "summary": notification.title,
            "sections": sections,
            "potentialAction": potential_action
        }
    
    def _get_activity_image(self, notification_type: str) -> str:
        """Get image URL for notification type"""
        # Use emoji data URLs or hosted images
        # For now, returning emoji as fallback
        return ""
