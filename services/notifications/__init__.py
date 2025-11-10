"""
Notification service initialization
"""
from .models import (
    EmailNotificationData,
    Notification,
    NotificationChannel,
    NotificationDelivery,
    NotificationPreferences,
    NotificationPriority,
    NotificationType,
    PushNotificationData,
    SlackNotificationData,
    TeamsNotificationData,
)
from .routes import router
from .service import NotificationService, get_notification_service

__all__ = [
    # Models
    "Notification",
    "NotificationChannel",
    "NotificationType",
    "NotificationPriority",
    "NotificationPreferences",
    "NotificationDelivery",
    "EmailNotificationData",
    "SlackNotificationData",
    "TeamsNotificationData",
    "PushNotificationData",
    # Service
    "NotificationService",
    "get_notification_service",
    # Router
    "router",
]
