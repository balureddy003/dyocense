"""
Notification service - Unified multi-channel notification system
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from .channels.base import NotificationChannel
from .channels.email import EmailChannel
from .channels.in_app import InAppChannel
from .channels.push import PushChannel
from .channels.slack import SlackChannel
from .channels.teams import TeamsChannel
from .models import (
    Notification,
    NotificationChannel as ChannelEnum,
    NotificationDelivery,
    NotificationPreferences,
    NotificationPriority,
    NotificationType,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Unified notification service supporting multiple channels
    
    Features:
    - Multi-channel delivery (email, push, Slack, Teams, in-app)
    - User preferences management
    - Quiet hours support
    - Priority-based routing
    - Delivery tracking
    - Async/batched sending
    """
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.channels: dict[ChannelEnum, NotificationChannel] = {}
        self._initialize_channels()
    
    def _initialize_channels(self):
        """Initialize enabled notification channels"""
        channel_configs = self.config.get('channels', {})
        
        # Email channel
        if channel_configs.get('email', {}).get('enabled'):
            self.channels[ChannelEnum.EMAIL] = EmailChannel(channel_configs['email'])
        
        # Push channel
        if channel_configs.get('push', {}).get('enabled'):
            self.channels[ChannelEnum.PUSH] = PushChannel(channel_configs['push'])
        
        # Slack channel
        if channel_configs.get('slack', {}).get('enabled'):
            self.channels[ChannelEnum.SLACK] = SlackChannel(channel_configs['slack'])
        
        # Teams channel
        if channel_configs.get('teams', {}).get('enabled'):
            self.channels[ChannelEnum.TEAMS] = TeamsChannel(channel_configs['teams'])
        
        # In-app channel
        if channel_configs.get('in_app', {}).get('enabled'):
            self.channels[ChannelEnum.IN_APP] = InAppChannel(channel_configs['in_app'])
        
        logger.info(f"Initialized {len(self.channels)} notification channels: {list(self.channels.keys())}")
    
    async def send_notification(
        self,
        tenant_id: str,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        channels: Optional[list[ChannelEnum]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> list[NotificationDelivery]:
        """
        Send notification through specified channels
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            channels: List of channels to send through (defaults to user preferences)
            priority: Notification priority
            data: Additional data for channel-specific formatting
            scheduled_at: Optional scheduled delivery time
            
        Returns:
            List of delivery status for each channel
        """
        # Create notification
        notification = Notification(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            channels=channels or [],
            scheduled_at=scheduled_at,
        )
        
        # Get user preferences
        user_prefs = await self._get_user_preferences(tenant_id, user_id)
        
        # Determine which channels to use
        target_channels = self._resolve_channels(notification, user_prefs)
        
        # Check quiet hours
        if self._is_quiet_hours(user_prefs):
            if priority != NotificationPriority.URGENT:
                logger.info(f"Skipping notification for {user_id} due to quiet hours")
                # TODO: Queue for later delivery
                return []
        
        # Send through each channel
        deliveries = []
        for channel_type in target_channels:
            channel = self.channels.get(channel_type)
            if channel and channel.enabled:
                try:
                    delivery = await channel.send(notification)
                    deliveries.append(delivery)
                except Exception as e:
                    logger.error(f"Error sending via {channel_type}: {e}")
                    deliveries.append(NotificationDelivery(
                        id=f"{notification.id}_{channel_type}_error",
                        notification_id=notification.id,
                        channel=channel_type,
                        status="failed",
                        error=str(e)
                    ))
        
        return deliveries
    
    async def send_goal_milestone(
        self,
        tenant_id: str,
        user_id: str,
        goal_title: str,
        percentage: int,
        recipient_email: Optional[str] = None,
    ):
        """Send goal milestone celebration notification"""
        milestone_messages = {
            25: "Great progress! You've reached 25% of your goal.",
            50: "Halfway there! You're crushing it! 🎉",
            75: "Amazing! You're 75% of the way to your goal!",
            100: "Goal achieved! Congratulations! 🏆",
        }
        
        data = {
            'goal_title': goal_title,
            'percentage': percentage,
            'action_url': f'{self.config.get("app_url", "")}/goals',
            'action_text': 'View Goals',
        }
        
        if recipient_email:
            data['recipient_email'] = recipient_email
        
        return await self.send_notification(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=NotificationType.GOAL_MILESTONE,
            title=f"🎯 Goal Milestone: {goal_title}",
            message=milestone_messages.get(percentage, f"{percentage}% complete!"),
            priority=NotificationPriority.MEDIUM,
            data=data,
        )
    
    async def send_streak_notification(
        self,
        tenant_id: str,
        user_id: str,
        weeks: int,
        recipient_email: Optional[str] = None,
    ):
        """Send streak milestone notification"""
        streak_messages = {
            1: "You completed your first week! 🎉",
            4: "1 month streak! You're on fire! 🔥",
            8: "2 months of consistency! Incredible! 💪",
            12: "3 months! You're unstoppable! 🏆",
        }
        
        data = {
            'weeks': weeks,
            'action_url': f'{self.config.get("app_url", "")}/home',
            'action_text': 'View Dashboard',
        }
        
        if recipient_email:
            data['recipient_email'] = recipient_email
        
        message = streak_messages.get(weeks, f"{weeks} weeks in a row! Keep going!")
        
        return await self.send_notification(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=NotificationType.STREAK,
            title=f"🔥 {weeks}-Week Streak!",
            message=message,
            priority=NotificationPriority.MEDIUM,
            data=data,
        )
    
    async def send_weekly_summary(
        self,
        tenant_id: str,
        user_id: str,
        summary_data: dict[str, Any],
        recipient_email: Optional[str] = None,
    ):
        """Send weekly summary notification"""
        tasks_completed = summary_data.get('tasks_completed', 0)
        health_score = summary_data.get('health_score', 0)
        
        message = f"This week: {tasks_completed} tasks completed, Health Score: {health_score}/100"
        
        data = {
            **summary_data,
            'action_url': f'{self.config.get("app_url", "")}/home',
            'action_text': 'View Full Report',
        }
        
        if recipient_email:
            data['recipient_email'] = recipient_email
        
        return await self.send_notification(
            tenant_id=tenant_id,
            user_id=user_id,
            notification_type=NotificationType.SUMMARY,
            title="📊 Your Weekly Summary",
            message=message,
            priority=NotificationPriority.LOW,
            data=data,
        )
    
    async def _get_user_preferences(
        self, tenant_id: str, user_id: str
    ) -> NotificationPreferences:
        """Get user notification preferences"""
        # TODO: Load from database
        # For now, return default preferences
        return NotificationPreferences(
            user_id=user_id,
            tenant_id=tenant_id,
            enabled_channels={
                ChannelEnum.EMAIL: True,
                ChannelEnum.IN_APP: True,
                ChannelEnum.PUSH: False,
                ChannelEnum.SLACK: False,
                ChannelEnum.TEAMS: False,
            }
        )
    
    def _resolve_channels(
        self,
        notification: Notification,
        preferences: NotificationPreferences,
    ) -> list[ChannelEnum]:
        """Resolve which channels to use based on notification and preferences"""
        if notification.channels:
            # Use explicitly specified channels
            return notification.channels
        
        # Use enabled channels from preferences
        enabled = [
            channel for channel, enabled in preferences.enabled_channels.items()
            if enabled and channel in self.channels
        ]
        
        # Always include in-app for high priority
        if notification.priority == NotificationPriority.HIGH and ChannelEnum.IN_APP not in enabled:
            enabled.append(ChannelEnum.IN_APP)
        
        return enabled
    
    def _is_quiet_hours(self, preferences: NotificationPreferences) -> bool:
        """Check if current time is within user's quiet hours"""
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False
        
        # TODO: Implement timezone-aware quiet hours check
        return False


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(config: Optional[dict[str, Any]] = None) -> NotificationService:
    """Get or create notification service singleton"""
    global _notification_service
    
    if _notification_service is None:
        if config is None:
            raise ValueError("Configuration required for first initialization")
        _notification_service = NotificationService(config)
    
    return _notification_service
