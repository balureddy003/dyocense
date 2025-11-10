"""
Push notification channel for web push
"""
import logging
from datetime import datetime
from typing import Any

from ..models import (
    Notification,
    NotificationChannel as ChannelEnum,
    NotificationDelivery,
)
from .base import NotificationChannel

logger = logging.getLogger(__name__)


class PushChannel(NotificationChannel):
    """Web push notification channel"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.vapid_private_key = config.get('vapid_private_key')
        self.vapid_public_key = config.get('vapid_public_key')
        self.vapid_claims = config.get('vapid_claims', {})
    
    def validate_config(self) -> bool:
        """Validate push configuration"""
        return bool(self.vapid_private_key and self.vapid_public_key)
    
    async def send(self, notification: Notification) -> NotificationDelivery:
        """Send web push notification"""
        delivery = NotificationDelivery(
            id=f"{notification.id or 'notification'}_push_{datetime.utcnow().timestamp()}",
            notification_id=notification.id or "",
            channel=ChannelEnum.PUSH,
            status="pending",
        )
        
        try:
            # Get push-specific data
            push_data = notification.data.get('push', {})
            subscription_info = push_data.get('subscription')
            
            if not subscription_info:
                raise ValueError("Push subscription info not provided")
            
            # Format push payload
            payload = self._format_push_payload(notification, push_data)
            
            # TODO: Integrate with pywebpush or similar library
            # from pywebpush import webpush
            # webpush(
            #     subscription_info=subscription_info,
            #     data=json.dumps(payload),
            #     vapid_private_key=self.vapid_private_key,
            #     vapid_claims=self.vapid_claims
            # )
            
            delivery.status = "sent"
            delivery.sent_at = datetime.utcnow()
            logger.info(f"Push notification sent: {notification.title}")
            
        except Exception as e:
            delivery.status = "failed"
            delivery.error = str(e)
            logger.error(f"Failed to send push notification: {e}")
        
        return delivery
    
    def _format_push_payload(self, notification: Notification, push_data: dict) -> dict:
        """Format notification as web push payload"""
        return {
            "title": notification.title,
            "body": notification.message,
            "icon": push_data.get('icon', '/logo-192.png'),
            "badge": push_data.get('badge', '/badge-72.png'),
            "tag": push_data.get('tag', notification.type),
            "data": {
                "url": notification.data.get('action_url', '/'),
                "notification_id": notification.id,
                **notification.data
            },
            "actions": push_data.get('actions', [
                {
                    "action": "view",
                    "title": "View"
                }
            ])
        }
