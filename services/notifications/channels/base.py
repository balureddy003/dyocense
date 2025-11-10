"""
Base notification channel interface
"""
from abc import ABC, abstractmethod
from typing import Any

from ..models import Notification, NotificationDelivery


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
    
    @abstractmethod
    async def send(self, notification: Notification) -> NotificationDelivery:
        """
        Send notification through this channel
        
        Args:
            notification: Notification to send
            
        Returns:
            NotificationDelivery with status and metadata
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate channel configuration"""
        pass
    
    def format_message(self, notification: Notification) -> dict[str, Any]:
        """
        Format notification for this channel
        Override in subclasses for channel-specific formatting
        """
        return {
            'title': notification.title,
            'message': notification.message,
            'data': notification.data,
        }
