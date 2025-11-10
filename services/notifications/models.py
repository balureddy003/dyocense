"""
Notification models for unified multi-channel notification system
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NotificationChannel(str, Enum):
    """Supported notification channels"""
    EMAIL = "email"
    PUSH = "push"
    SLACK = "slack"
    TEAMS = "teams"
    IN_APP = "in_app"
    SMS = "sms"


class NotificationType(str, Enum):
    """Notification types aligned with celebration system"""
    GOAL_MILESTONE = "goal_milestone"
    TASK_COMPLETE = "task_complete"
    WEEK_COMPLETE = "week_complete"
    HEALTH_SCORE = "health_score"
    STREAK = "streak"
    NUDGE = "nudge"
    ALERT = "alert"
    SUMMARY = "summary"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    """Priority levels for notification delivery"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """Core notification model"""
    id: Optional[str] = None
    tenant_id: str
    user_id: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    channels: list[NotificationChannel] = Field(default_factory=list)
    scheduled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationPreferences(BaseModel):
    """User notification channel preferences"""
    user_id: str
    tenant_id: str
    enabled_channels: dict[NotificationChannel, bool] = Field(default_factory=dict)
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None
    timezone: str = "UTC"
    
    # Notification type preferences
    type_preferences: dict[NotificationType, dict[str, Any]] = Field(default_factory=dict)


class NotificationDelivery(BaseModel):
    """Delivery status tracking"""
    id: str
    notification_id: str
    channel: NotificationChannel
    status: str  # pending, sent, delivered, failed
    error: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmailNotificationData(BaseModel):
    """Email-specific notification data"""
    subject: str
    body_html: str
    body_text: str
    from_email: str = "Dyocense Coach <coach@dyocense.com>"
    reply_to: Optional[str] = None
    attachments: list[dict[str, str]] = Field(default_factory=list)


class SlackNotificationData(BaseModel):
    """Slack-specific notification data"""
    webhook_url: str
    channel: Optional[str] = None
    username: str = "Dyocense Coach"
    icon_emoji: str = ":chart_with_upwards_trend:"
    blocks: Optional[list[dict[str, Any]]] = None


class TeamsNotificationData(BaseModel):
    """Microsoft Teams-specific notification data"""
    webhook_url: str
    title: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    theme_color: str = "0078D4"


class PushNotificationData(BaseModel):
    """Web push notification data"""
    title: str
    body: str
    icon: Optional[str] = None
    badge: Optional[str] = None
    tag: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)
    actions: list[dict[str, str]] = Field(default_factory=list)
