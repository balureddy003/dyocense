"""
Slack notification channel using webhooks
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


class SlackChannel(NotificationChannel):
    """Slack notification channel via webhooks"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.default_webhook_url = config.get('webhook_url')
        self.default_channel = config.get('channel')
        self.username = config.get('username', 'Dyocense Coach')
        self.icon_emoji = config.get('icon_emoji', ':chart_with_upwards_trend:')
    
    def validate_config(self) -> bool:
        """Validate Slack configuration"""
        return bool(self.default_webhook_url)
    
    async def send(self, notification: Notification) -> NotificationDelivery:
        """Send Slack notification"""
        delivery = NotificationDelivery(
            id=f"{notification.id or 'notification'}_slack_{datetime.utcnow().timestamp()}",
            notification_id=notification.id or "",
            channel=ChannelEnum.SLACK,
            status="pending",
        )
        
        try:
            # Get Slack-specific data
            slack_data = notification.data.get('slack', {})
            webhook_url = slack_data.get('webhook_url', self.default_webhook_url)
            
            if not webhook_url:
                raise ValueError("Slack webhook URL not provided")
            
            # Format message
            payload = self._format_slack_message(notification, slack_data)
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        delivery.status = "sent"
                        delivery.sent_at = datetime.utcnow()
                        logger.info(f"Slack notification sent: {notification.title}")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Slack API error: {response.status} - {error_text}")
        
        except Exception as e:
            delivery.status = "failed"
            delivery.error = str(e)
            logger.error(f"Failed to send Slack notification: {e}")
        
        return delivery
    
    def _format_slack_message(self, notification: Notification, slack_data: dict) -> dict:
        """Format notification as Slack message with blocks"""
        blocks = slack_data.get('blocks')
        
        if not blocks:
            # Generate default blocks based on notification type
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{self._get_emoji(notification.type)} {notification.title}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": notification.message
                    }
                }
            ]
            
            # Add action button if provided
            action_url = notification.data.get('action_url')
            if action_url:
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": notification.data.get('action_text', 'View Dashboard'),
                                "emoji": True
                            },
                            "url": action_url,
                            "style": "primary"
                        }
                    ]
                })
        
        return {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "channel": slack_data.get('channel', self.default_channel),
            "blocks": blocks
        }
    
    def _get_emoji(self, notification_type: str) -> str:
        """Get emoji for notification type"""
        emoji_map = {
            'goal_milestone': '🎯',
            'task_complete': '✅',
            'week_complete': '🎉',
            'health_score': '💪',
            'streak': '🔥',
            'nudge': '👋',
            'alert': '⚠️',
            'summary': '📊',
            'system': '🔔',
        }
        return emoji_map.get(notification_type, '📢')
