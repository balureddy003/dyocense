from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Tuple

import jwt

from packages.kernel_common.persistence import get_collection

from .models import (
    AccountUser,
    ApiTokenRecord,
    Invitation,
    PlanLimits,
    PlanTier,
    Project,
    SubscriptionPlan,
    Tenant,
    TenantUsage,
    UsageEvent,
)


class SubscriptionLimitError(RuntimeError):
    """Raised when a tenant exceeds its subscription capacity."""


class AuthenticationError(RuntimeError):
    """Raised when user authentication fails."""


PLAN_CATALOG: List[SubscriptionPlan] = [
    SubscriptionPlan(
        tier=PlanTier.FREE,
        name="Starter",
        price_per_month=49.0,
        description="Perfect for single-location businesses getting started.",
        limits=PlanLimits(
            max_projects=1,  # 1 location/business unit
            max_playbooks=10,  # 10 decisions per month
            max_members=3,
            support_level="Email"
        ),
        features=[
            "1 location or business unit",
            "10 business decisions per month",
            "3 team members",
            "Email support",
            "Basic templates & integrations",
            "7-day free trial",
        ],
    ),
    SubscriptionPlan(
        tier=PlanTier.SILVER,
        name="Growth",
        price_per_month=199.0,
        description="For businesses ready to scale operations.",
        limits=PlanLimits(
            max_projects=3,  # 3 locations
            max_playbooks=50,  # 50 decisions per month
            max_members=10,
            support_level="Priority + Chat"
        ),
        features=[
            "Up to 3 locations",
            "50 business decisions per month",
            "10 team members",
            "Priority support + chat",
            "Advanced analytics & forecasting",
            "API access for integrations",
            "Custom data connectors",
        ],
    ),
    SubscriptionPlan(
        tier=PlanTier.GOLD,
        name="Business",
        price_per_month=499.0,
        description="For multi-location operations with dedicated support.",
        limits=PlanLimits(
            max_projects=10,  # 10 locations
            max_playbooks=200,  # 200 decisions per month
            max_members=25,
            support_level="Dedicated Success Manager"
        ),
        features=[
            "Up to 10 locations",
            "200 business decisions per month",
            "25 team members",
            "Dedicated success manager",
            "Custom integrations & workflows",
            "SSO & advanced security",
            "White-label options",
        ],
    ),
    SubscriptionPlan(
        tier=PlanTier.PLATINUM,
        name="Enterprise",
        price_per_month=1999.0,
        description="Unlimited scale with enterprise-grade support and customization.",
        limits=PlanLimits(
            max_projects=100,  # Unlimited for practical purposes
            max_playbooks=1000,  # High limit
            max_members=100,
            support_level="24/7 Enterprise + Solution Architect"
        ),
        features=[
            "Unlimited locations",
            "Unlimited business decisions",
            "Unlimited team members",
            "24/7 priority support",
            "Dedicated solution architect",
            "Custom development",
            "SLA guarantees",
            "On-premise deployment option",
        ],
    ),
]


TENANT_COLLECTION = get_collection("tenants")
PROJECT_COLLECTION = get_collection("projects")
USERS_COLLECTION = get_collection("tenant_users")
TOKENS_COLLECTION = get_collection("user_tokens")
INVITES_COLLECTION = get_collection("invitations")
EVENTS_COLLECTION = get_collection("usage_events")

JWT_SECRET = os.getenv("ACCOUNTS_JWT_SECRET", "dyocense-dev-secret")
JWT_ISSUER = "dyocense-accounts"
JWT_TTL_MINUTES = int(os.getenv("ACCOUNTS_JWT_TTL", "60"))
JWT_TTL_SECONDS = JWT_TTL_MINUTES * 60

# Admin tenant for privileged operations
ADMIN_TENANT_ID = os.getenv("ADMIN_TENANT_ID", "admin-dyocense")


def list_plans() -> List[SubscriptionPlan]:
    return PLAN_CATALOG


def get_plan(tier: PlanTier) -> SubscriptionPlan:
    for plan in PLAN_CATALOG:
        if plan.tier == tier:
            return plan
    raise ValueError(f"Unknown plan tier: {tier}")


def _slugify_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "tenant"


def _now() -> datetime:
    return datetime.utcnow()


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _generate_password_hash(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 390000)
    return salt, base64.b64encode(dk).decode("utf-8")


def _verify_password(password: str, salt: str, hashed: str) -> bool:
    _, new_hash = _generate_password_hash(password, salt)
    return hmac.compare_digest(new_hash, hashed)


def _tenant_from_doc(document: dict) -> Tenant:
    usage_doc = document.get("usage") or {}
    usage = TenantUsage(
        projects=usage_doc.get("projects", 0),
        playbooks=usage_doc.get("playbooks", 0),
        members=usage_doc.get("members", 1),
        cycle_started_at=datetime.fromisoformat(usage_doc.get("cycle_started_at"))
        if usage_doc.get("cycle_started_at")
        else _now(),
    )
    return Tenant(
        tenant_id=document["tenant_id"],
        name=document["name"],
        owner_email=document["owner_email"],
        plan_tier=PlanTier(document["plan_tier"]),
        status=document.get("status", "active"),
        api_token=document["api_token"],
        created_at=datetime.fromisoformat(document["created_at"]),
        updated_at=datetime.fromisoformat(document["updated_at"]),
        metadata=document.get("metadata", {}),
        usage=usage,
    )


def _tenant_to_doc(tenant: Tenant) -> dict:
    return {
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "owner_email": tenant.owner_email,
        "plan_tier": tenant.plan_tier.value,
        "status": tenant.status,
        "api_token": tenant.api_token,
        "created_at": tenant.created_at.isoformat(),
        "updated_at": tenant.updated_at.isoformat(),
        "metadata": tenant.metadata,
        "usage": {
            "projects": tenant.usage.projects,
            "playbooks": tenant.usage.playbooks,
            "members": tenant.usage.members,
            "cycle_started_at": tenant.usage.cycle_started_at.isoformat(),
        },
    }


def _project_from_doc(document: dict) -> Project:
    return Project(
        tenant_id=document["tenant_id"],
        project_id=document["project_id"],
        name=document["name"],
        description=document.get("description"),
        created_at=datetime.fromisoformat(document["created_at"]),
        updated_at=datetime.fromisoformat(document["updated_at"]),
    )


def _project_to_doc(project: Project) -> dict:
    return {
        "tenant_id": project.tenant_id,
        "project_id": project.project_id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def register_tenant(name: str, owner_email: str, plan_tier: PlanTier, metadata: Optional[dict] = None) -> Tenant:
    metadata = metadata or {}
    tenant_id = f"{_slugify_name(name)}-{uuid.uuid4().hex[:6]}"
    api_token = f"key-{secrets.token_urlsafe(16)}"
    now = _now()
    tenant = Tenant(
        tenant_id=tenant_id,
        name=name,
        owner_email=owner_email,
        plan_tier=plan_tier,
        status="active",
        api_token=api_token,
        created_at=now,
        updated_at=now,
        metadata=metadata,
        usage=TenantUsage(),
    )
    TENANT_COLLECTION.replace_one({"tenant_id": tenant.tenant_id}, _tenant_to_doc(tenant), upsert=True)
    return tenant


def get_tenant(tenant_id: str) -> Optional[Tenant]:
    document = TENANT_COLLECTION.find_one({"tenant_id": tenant_id})
    if not document:
        return None
    return _tenant_from_doc(document)


def get_tenant_by_token(api_token: str) -> Optional[Tenant]:
    document = TENANT_COLLECTION.find_one({"api_token": api_token})
    if not document:
        return None
    return _tenant_from_doc(document)


def update_tenant_plan(tenant_id: str, plan_tier: PlanTier) -> Tenant:
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise ValueError(f"Tenant {tenant_id} not found")
    tenant.plan_tier = plan_tier
    tenant.updated_at = _now()
    TENANT_COLLECTION.replace_one({"tenant_id": tenant.tenant_id}, _tenant_to_doc(tenant), upsert=True)
    return tenant


def _count_projects(tenant_id: str) -> int:
    return sum(1 for _ in _iterate(PROJECT_COLLECTION.find({"tenant_id": tenant_id})))


def _iterate(cursor: Iterable[dict]) -> Iterable[dict]:
    for item in cursor:
        yield item


def ensure_usage_limits(tenant: Tenant) -> None:
    plan = get_plan(tenant.plan_tier)
    if tenant.usage.projects > plan.limits.max_projects:
        raise SubscriptionLimitError("Project limit reached for current plan.")
    if tenant.usage.playbooks > plan.limits.max_playbooks:
        raise SubscriptionLimitError("Playbook storage limit reached for current plan.")
    if tenant.usage.members > plan.limits.max_members:
        raise SubscriptionLimitError("Seat allocation exceeded for current plan.")


def create_project(tenant_id: str, name: str, description: Optional[str] = None) -> Project:
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise ValueError("Tenant not found")

    plan = get_plan(tenant.plan_tier)
    current_project_count = _count_projects(tenant_id)
    if current_project_count >= plan.limits.max_projects:
        raise SubscriptionLimitError("Project limit reached for current subscription tier.")

    project = Project(
        tenant_id=tenant_id,
        project_id=f"proj-{uuid.uuid4().hex[:8]}",
        name=name,
        description=description,
        created_at=_now(),
        updated_at=_now(),
    )
    PROJECT_COLLECTION.insert_one(_project_to_doc(project))
    tenant.usage.projects = current_project_count + 1
    tenant.updated_at = _now()
    TENANT_COLLECTION.replace_one({"tenant_id": tenant.tenant_id}, _tenant_to_doc(tenant), upsert=True)
    return project


def list_projects(tenant_id: str) -> List[Project]:
    return [_project_from_doc(doc) for doc in PROJECT_COLLECTION.find({"tenant_id": tenant_id})]


def record_playbook_usage(tenant_id: str, increment: int = 1) -> Tenant:
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise ValueError("Tenant not found")
    plan = get_plan(tenant.plan_tier)
    if tenant.usage.playbooks + increment > plan.limits.max_playbooks:
        raise SubscriptionLimitError("Playbook storage limit reached for current plan.")
    tenant.usage.playbooks += increment
    tenant.updated_at = _now()
    TENANT_COLLECTION.replace_one({"tenant_id": tenant.tenant_id}, _tenant_to_doc(tenant), upsert=True)
    return tenant


# ---- User management ---------------------------------------------------------------------------


def _user_from_doc(document: dict) -> AccountUser:
    return AccountUser(
        user_id=document["user_id"],
        tenant_id=document["tenant_id"],
        email=document["email"],
        full_name=document["full_name"],
        password_hash=document["password_hash"],
        created_at=datetime.fromisoformat(document["created_at"]),
        updated_at=datetime.fromisoformat(document["updated_at"]),
        roles=document.get("roles", ["member"]),
            oauth_provider=document.get("oauth_provider"),
            oauth_provider_id=document.get("oauth_provider_id"),
            picture_url=document.get("picture_url"),
    )


def _user_to_doc(user: AccountUser) -> dict:
    doc = {
        "user_id": user.user_id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "full_name": user.full_name,
        "password_hash": user.password_hash,
        "roles": user.roles,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }
    # Add OAuth fields if present
    if user.oauth_provider:
        doc["oauth_provider"] = user.oauth_provider
    if user.oauth_provider_id:
        doc["oauth_provider_id"] = user.oauth_provider_id
    if user.picture_url:
        doc["picture_url"] = user.picture_url
    return doc


def register_user(tenant_id: str, email: str, full_name: str, password: str) -> AccountUser:
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise ValueError("Tenant not found")

    existing = USERS_COLLECTION.find_one({"tenant_id": tenant_id, "email": email.lower()})
    if existing:
        raise AuthenticationError("User already exists for this tenant.")

    salt, password_hash = _generate_password_hash(password)
    user = AccountUser(
        user_id=f"user-{uuid.uuid4().hex[:10]}",
        tenant_id=tenant_id,
        email=email.lower(),
        full_name=full_name,
        password_hash=f"{salt}:{password_hash}",
        created_at=_now(),
        updated_at=_now(),
        roles=["member"],
    )
    USERS_COLLECTION.insert_one(_user_to_doc(user))
    tenant.usage.members += 1
    tenant.updated_at = _now()
    TENANT_COLLECTION.replace_one({"tenant_id": tenant.tenant_id}, _tenant_to_doc(tenant), upsert=True)
    return user


def get_user_by_email(tenant_id: str, email: str) -> Optional[AccountUser]:
    document = USERS_COLLECTION.find_one({"tenant_id": tenant_id, "email": email.lower()})
    if not document:
        return None
    return _user_from_doc(document)


def get_user(user_id: str) -> Optional[AccountUser]:
    document = USERS_COLLECTION.find_one({"user_id": user_id})
    if not document:
        return None
    return _user_from_doc(document)


def authenticate_user(tenant_id: str, email: str, password: str) -> AccountUser:
    user = get_user_by_email(tenant_id, email)
    if user is None:
        raise AuthenticationError("Incorrect email or password.")
    try:
        salt, stored_hash = user.password_hash.split(":", 1)
    except ValueError as exc:
        raise AuthenticationError("Stored password invalid.") from exc
    if not _verify_password(password, salt, stored_hash):
        raise AuthenticationError("Incorrect email or password.")
    return user


def count_users_for_tenant(tenant_id: str) -> int:
    """Return the number of users that exist for a given tenant.

    Used to allow a safe fallback for first-user registration when no temporary
    password was issued during onboarding.
    """
    try:
        return USERS_COLLECTION.count_documents({"tenant_id": tenant_id})
    except Exception:
        # In-memory fallback or collection not available; attempt len on list-like
        try:
            return len(list(USERS_COLLECTION.find({"tenant_id": tenant_id})))
        except Exception:
            return 0


def find_tenants_for_email(email: str) -> list[str]:
    """
    Find all tenant IDs where a user with the given email exists.
    Returns a list of tenant IDs.
    """
    try:
        # Find all users with this email across all tenants
        users = USERS_COLLECTION.find({"email": email.lower()})
        tenant_ids = []
        for user_doc in users:
            if "tenant_id" in user_doc:
                tenant_ids.append(user_doc["tenant_id"])
        return tenant_ids
    except Exception:
        return []


def update_user_password(user_id: str, password: str) -> AccountUser:
    user = get_user(user_id)
    if user is None:
        raise ValueError("User not found")
    salt, password_hash = _generate_password_hash(password)
    user.password_hash = f"{salt}:{password_hash}"
    user.updated_at = _now()
    USERS_COLLECTION.replace_one({"user_id": user.user_id}, _user_to_doc(user), upsert=True)
    return user


def _token_from_doc(document: dict) -> ApiTokenRecord:
    return ApiTokenRecord(
        token_id=document["token_id"],
        tenant_id=document["tenant_id"],
        user_id=document["user_id"],
        name=document["name"],
        secret_hash=document["secret_hash"],
        created_at=datetime.fromisoformat(document["created_at"]),
    )


def _token_to_doc(token: ApiTokenRecord) -> dict:
    return {
        "token_id": token.token_id,
        "tenant_id": token.tenant_id,
        "user_id": token.user_id,
        "name": token.name,
        "secret_hash": token.secret_hash,
        "created_at": token.created_at.isoformat(),
    }


def list_api_tokens(tenant_id: str, user_id: str) -> List[ApiTokenRecord]:
    return [
        _token_from_doc(doc)
        for doc in TOKENS_COLLECTION.find({"tenant_id": tenant_id, "user_id": user_id})
    ]


def create_api_token(tenant_id: str, user_id: str, name: str) -> Tuple[str, ApiTokenRecord]:
    token_secret = f"key-{secrets.token_urlsafe(16)}"
    record = ApiTokenRecord(
        token_id=f"tok-{uuid.uuid4().hex[:10]}",
        tenant_id=tenant_id,
        user_id=user_id,
        name=name or "API token",
        secret_hash=_hash_secret(token_secret),
        created_at=_now(),
    )
    TOKENS_COLLECTION.insert_one(_token_to_doc(record))
    return token_secret, record


def delete_api_token(token_id: str, tenant_id: str, user_id: str) -> bool:
    result = TOKENS_COLLECTION.delete_one({"token_id": token_id, "tenant_id": tenant_id, "user_id": user_id})
    return result.deleted_count > 0


def get_api_token(secret: str) -> Optional[ApiTokenRecord]:
    hashed = _hash_secret(secret)
    document = TOKENS_COLLECTION.find_one({"secret_hash": hashed})
    if not document:
        return None
    return _token_from_doc(document)


def issue_jwt(user: AccountUser) -> str:
    now = _now()
    payload = {
        "iss": JWT_ISSUER,
        "sub": user.user_id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "name": user.full_name,
        "roles": user.roles,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_TTL_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def decode_jwt(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], issuer=JWT_ISSUER)
        return payload
    except jwt.PyJWTError:
        return None


# ---- Invitations --------------------------------------------------------------------------------


def _invitation_from_doc(document: dict) -> Invitation:
    return Invitation(
        invite_id=document["invite_id"],
        tenant_id=document["tenant_id"],
        inviter_user_id=document["inviter_user_id"],
        invitee_email=document["invitee_email"],
        status=document.get("status", "pending"),
        created_at=datetime.fromisoformat(document["created_at"]),
        expires_at=datetime.fromisoformat(document["expires_at"]),
    )


def _invitation_to_doc(invite: Invitation) -> dict:
    return {
        "invite_id": invite.invite_id,
        "tenant_id": invite.tenant_id,
        "inviter_user_id": invite.inviter_user_id,
        "invitee_email": invite.invitee_email,
        "status": invite.status,
        "created_at": invite.created_at.isoformat(),
        "expires_at": invite.expires_at.isoformat(),
    }


def create_invitation(tenant_id: str, inviter_user_id: str, invitee_email: str, expires_days: int = 7) -> Invitation:
    """Create a team invitation token."""
    invite = Invitation(
        invite_id=f"inv-{uuid.uuid4().hex[:10]}",
        tenant_id=tenant_id,
        inviter_user_id=inviter_user_id,
        invitee_email=invitee_email.lower(),
        status="pending",
        created_at=_now(),
        expires_at=_now() + timedelta(days=expires_days),
    )
    INVITES_COLLECTION.insert_one(_invitation_to_doc(invite))
    return invite


def get_invitation(invite_id: str) -> Optional[Invitation]:
    document = INVITES_COLLECTION.find_one({"invite_id": invite_id})
    if not document:
        return None
    return _invitation_from_doc(document)


def list_invitations(tenant_id: str, status: Optional[str] = None) -> List[Invitation]:
    """List invitations for a tenant, optionally filtered by status."""
    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    return [_invitation_from_doc(doc) for doc in INVITES_COLLECTION.find(query)]


def accept_invitation(invite_id: str) -> Invitation:
    """Mark invitation as accepted."""
    invite = get_invitation(invite_id)
    if not invite:
        raise ValueError("Invitation not found")
    if invite.status != "pending":
        raise ValueError(f"Invitation already {invite.status}")
    if _now() > invite.expires_at:
        invite.status = "expired"
        INVITES_COLLECTION.replace_one({"invite_id": invite.invite_id}, _invitation_to_doc(invite))
        raise ValueError("Invitation expired")
    invite.status = "accepted"
    INVITES_COLLECTION.replace_one({"invite_id": invite.invite_id}, _invitation_to_doc(invite))
    return invite


def revoke_invitation(invite_id: str, tenant_id: str) -> Invitation:
    """Revoke a pending invitation."""
    invite = get_invitation(invite_id)
    if not invite:
        raise ValueError("Invitation not found")
    if invite.tenant_id != tenant_id:
        raise ValueError("Invitation does not belong to this tenant")
    if invite.status != "pending":
        raise ValueError(f"Cannot revoke invitation with status: {invite.status}")
    invite.status = "revoked"
    INVITES_COLLECTION.replace_one({"invite_id": invite.invite_id}, _invitation_to_doc(invite))
    return invite


# ---- Admin & analytics ---------------------------------------------------------------------------


def list_all_tenants(limit: int = 100, skip: int = 0) -> List[Tenant]:
    """Admin only: list all tenants."""
    return [_tenant_from_doc(doc) for doc in TENANT_COLLECTION.find().skip(skip).limit(limit)]


def count_tenants() -> int:
    """Admin only: count all tenants."""
    return sum(1 for _ in _iterate(TENANT_COLLECTION.find()))


def record_usage_event(tenant_id: str, event_type: str, payload: Optional[dict] = None, user_id: Optional[str] = None) -> UsageEvent:
    """Log a usage event for analytics."""
    event = UsageEvent(
        event_id=f"evt-{uuid.uuid4().hex[:10]}",
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        payload=payload or {},
        timestamp=_now(),
    )
    EVENTS_COLLECTION.insert_one({
        "event_id": event.event_id,
        "tenant_id": event.tenant_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "payload": event.payload,
        "timestamp": event.timestamp.isoformat(),
    })
    return event


def get_usage_summary(tenant_id: Optional[str] = None, days: int = 30) -> dict:
    """Admin analytics: usage summary."""
    cutoff = _now() - timedelta(days=days)
    query = {"timestamp": {"$gte": cutoff.isoformat()}}
    if tenant_id:
        query["tenant_id"] = tenant_id

    events = list(EVENTS_COLLECTION.find(query))
    by_type: dict = {}
    for event in events:
        et = event.get("event_type", "unknown")
        by_type[et] = by_type.get(et, 0) + 1

    return {
        "period_days": days,
        "total_events": len(events),
        "by_type": by_type,
        "tenant_id": tenant_id,
    }


def find_tenant_by_name_or_email(name: str = None, owner_email: str = None) -> Optional[Tenant]:
    """
    Find an existing tenant by organization name AND owner email.
    This checks if the same person is trying to register the same organization again.
    Returns the matching tenant if found, None otherwise.
    """
    if not name or not owner_email:
        return None
    
    # Only match if BOTH the organization name AND owner email match
    # This allows the same person to create multiple organizations
    # but prevents duplicate organization registrations by the same person
    query = {
        "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"},
        "owner_email": owner_email.lower()
    }
    
    document = TENANT_COLLECTION.find_one(query)
    if not document:
        return None
    return _tenant_from_doc(document)


def enforce_trial_for_tenant(tenant_id: str, trial_days: int = 14) -> Tenant:
    """Auto-downgrade from trial (silver) to free if trial expired."""
    tenant = get_tenant(tenant_id)
    if not tenant:
        raise ValueError("Tenant not found")

    if tenant.plan_tier != PlanTier.SILVER:
        return tenant

    trial_ends = tenant.created_at + timedelta(days=trial_days)
    if _now() > trial_ends:
        tenant.plan_tier = PlanTier.FREE
        tenant.updated_at = _now()
        TENANT_COLLECTION.replace_one({"tenant_id": tenant.tenant_id}, _tenant_to_doc(tenant))
    return tenant
