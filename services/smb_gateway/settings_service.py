"""
Settings Persistence Service

Provides tenant settings storage and retrieval.
Business-agnostic design - works for any SMB.
"""

from typing import Dict, Optional
from pydantic import BaseModel


class NotificationSettings(BaseModel):
    """Notification preferences"""
    email_enabled: bool = True
    push_enabled: bool = False
    slack_enabled: bool = False
    teams_enabled: bool = False
    in_app_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    goal_milestones: bool = True
    task_completions: bool = True
    weekly_recap: bool = True
    nudges: bool = True
    alerts: bool = True


class AccountSettings(BaseModel):
    """Account information"""
    name: str = "Business Owner"
    email: str = ""
    business_name: str = ""
    timezone: str = "America/Los_Angeles"


class AppearanceSettings(BaseModel):
    """Appearance preferences"""
    theme: str = "light"  # 'light', 'dark', 'auto'
    color_scheme: str = "blue"


class IntegrationSettings(BaseModel):
    """Integration configuration"""
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    email_notifications_email: Optional[str] = None


class TenantSettings(BaseModel):
    """Complete tenant settings"""
    tenant_id: str
    notifications: NotificationSettings = NotificationSettings()
    account: AccountSettings = AccountSettings()
    appearance: AppearanceSettings = AppearanceSettings()
    integrations: IntegrationSettings = IntegrationSettings()


class SettingsService:
    """Service for managing tenant settings"""
    
    def __init__(self):
        # Storage: tenant_id -> TenantSettings
        self.settings_store: Dict[str, TenantSettings] = {}
    
    def get_settings(self, tenant_id: str) -> TenantSettings:
        """Get all settings for tenant"""
        if tenant_id not in self.settings_store:
            # Initialize with defaults
            self.settings_store[tenant_id] = TenantSettings(
                tenant_id=tenant_id,
                notifications=NotificationSettings(),
                account=AccountSettings(),
                appearance=AppearanceSettings(),
                integrations=IntegrationSettings(),
            )
        
        return self.settings_store[tenant_id]
    
    def update_notifications(
        self,
        tenant_id: str,
        settings: NotificationSettings
    ) -> TenantSettings:
        """Update notification settings"""
        current = self.get_settings(tenant_id)
        current.notifications = settings
        self.settings_store[tenant_id] = current
        return current
    
    def update_account(
        self,
        tenant_id: str,
        settings: AccountSettings
    ) -> TenantSettings:
        """Update account settings"""
        current = self.get_settings(tenant_id)
        current.account = settings
        self.settings_store[tenant_id] = current
        return current
    
    def update_appearance(
        self,
        tenant_id: str,
        settings: AppearanceSettings
    ) -> TenantSettings:
        """Update appearance settings"""
        current = self.get_settings(tenant_id)
        current.appearance = settings
        self.settings_store[tenant_id] = current
        return current
    
    def update_integrations(
        self,
        tenant_id: str,
        settings: IntegrationSettings
    ) -> TenantSettings:
        """Update integration settings"""
        current = self.get_settings(tenant_id)
        current.integrations = settings
        self.settings_store[tenant_id] = current
        return current
    
    def update_all_settings(
        self,
        tenant_id: str,
        settings: TenantSettings
    ) -> TenantSettings:
        """Update all settings at once"""
        settings.tenant_id = tenant_id
        self.settings_store[tenant_id] = settings
        return settings


# Global service instance
_settings_service: Optional[SettingsService] = None


def get_settings_service() -> SettingsService:
    """Get or create settings service singleton"""
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service
