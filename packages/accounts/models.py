from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PlanTier(str, Enum):
    FREE = "free"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class PlanLimits(BaseModel):
    max_projects: int = Field(..., description="Number of active projects allowed for the tenant.")
    max_playbooks: int = Field(..., description="Number of stored playbooks allowed for the tenant.")
    max_members: int = Field(..., description="Maximum number of user seats.")
    support_level: str = Field(..., description="Support tier description.")


class SubscriptionPlan(BaseModel):
    tier: PlanTier
    name: str
    price_per_month: float
    description: str
    limits: PlanLimits
    features: List[str] = Field(default_factory=list)


class TenantUsage(BaseModel):
    projects: int = 0
    playbooks: int = 0
    members: int = 1
    cycle_started_at: datetime = Field(default_factory=datetime.utcnow)


class Tenant(BaseModel):
    tenant_id: str
    name: str
    owner_email: str
    plan_tier: PlanTier
    status: str = "active"
    api_token: str
    created_at: datetime
    updated_at: datetime
    metadata: dict = Field(default_factory=dict)
    usage: TenantUsage = Field(default_factory=TenantUsage)


class Project(BaseModel):
    tenant_id: str
    project_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AccountUser(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    full_name: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
    roles: List[str] = Field(default_factory=lambda: ["member"])
    # OAuth fields
    oauth_provider: Optional[str] = None  # "google", "microsoft", "apple"
    oauth_provider_id: Optional[str] = None  # Provider's unique user ID
    picture_url: Optional[str] = None  # Profile picture from OAuth provider


class ApiTokenRecord(BaseModel):
    token_id: str
    tenant_id: str
    user_id: str
    name: str
    secret_hash: str
    created_at: datetime


class Invitation(BaseModel):
    """Team invitation with expiry and status tracking."""
    invite_id: str
    tenant_id: str
    inviter_user_id: str
    invitee_email: str
    status: str = "pending"  # pending, accepted, expired
    created_at: datetime
    expires_at: datetime


class UsageEvent(BaseModel):
    """Client or system usage event for analytics."""
    event_id: str
    tenant_id: str
    user_id: Optional[str] = None
    event_type: str
    payload: dict = Field(default_factory=dict)
    timestamp: datetime
