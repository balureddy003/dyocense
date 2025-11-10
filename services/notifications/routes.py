"""
Notification service FastAPI routes
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .models import NotificationChannel, NotificationPriority, NotificationType
from .service import get_notification_service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class SendNotificationRequest(BaseModel):
    """Request to send notification"""
    tenant_id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    channels: Optional[list[NotificationChannel]] = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: dict[str, Any] = {}
    scheduled_at: Optional[datetime] = None


class NotificationPreferencesRequest(BaseModel):
    """Update notification preferences"""
    enabled_channels: dict[NotificationChannel, bool]
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: str = "UTC"


@router.post("/send")
async def send_notification(request: SendNotificationRequest):
    """Send notification through specified channels"""
    try:
        service = get_notification_service()
        deliveries = await service.send_notification(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            notification_type=request.type,
            title=request.title,
            message=request.message,
            channels=request.channels,
            priority=request.priority,
            data=request.data,
            scheduled_at=request.scheduled_at,
        )
        
        return {
            "success": True,
            "deliveries": [
                {
                    "channel": d.channel,
                    "status": d.status,
                    "error": d.error,
                    "sent_at": d.sent_at,
                }
                for d in deliveries
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/{user_id}")
async def update_preferences(user_id: str, request: NotificationPreferencesRequest):
    """Update user notification preferences"""
    # TODO: Save to database
    return {
        "success": True,
        "message": "Preferences updated successfully"
    }


@router.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    """Get user notification preferences"""
    # TODO: Load from database
    return {
        "enabled_channels": {
            "email": True,
            "push": False,
            "slack": False,
            "teams": False,
            "in_app": True,
        },
        "quiet_hours_start": None,
        "quiet_hours_end": None,
        "timezone": "UTC",
    }


@router.get("/history/{user_id}")
async def get_notification_history(user_id: str, limit: int = 50):
    """Get notification history for user"""
    # TODO: Load from database
    return {
        "notifications": [],
        "total": 0,
    }
