from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Tuple, Any

import jwt
from psycopg2.extras import Json, RealDictCursor

from packages.kernel_common.persistence_v2 import get_backend, PostgresBackend

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


_backend = get_backend()
if not isinstance(_backend, PostgresBackend):
    raise RuntimeError(
        "Accounts repository requires Postgres backend. "
        "Set PERSISTENCE_BACKEND=postgres and configure POSTGRES_* env vars."
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


def _plan_from_db(value: str) -> PlanTier:
    """Map stored plan tier strings to PlanTier enum."""
    if not value:
        return PlanTier.FREE
    try:
        return PlanTier(value)
    except ValueError:
        legacy_map = {
            "smb_starter": PlanTier.FREE,
            "smb_growth": PlanTier.SILVER,
            "enterprise": PlanTier.PLATINUM,
        }
        return legacy_map.get(value, PlanTier.FREE)


def _plan_to_db(tier: PlanTier) -> str:
    return tier.value


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        # Normalize to naive UTC for internal comparisons
        if value.tzinfo is not None and value.utcoffset() is not None:
            from datetime import timezone as _dt_timezone
            return value.astimezone(_dt_timezone.utc).replace(tzinfo=None)
        return value
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is not None and dt.utcoffset() is not None:
                from datetime import timezone as _dt_timezone
                dt = dt.astimezone(_dt_timezone.utc).replace(tzinfo=None)
            return dt
        except ValueError:
            pass
    return _now()


def _usage_from_record(record: Optional[dict]) -> TenantUsage:
    record = record or {}
    cycle_value = record.get("cycle_started_at")
    return TenantUsage(
        projects=record.get("projects") or record.get("projects_count", 0),
        playbooks=record.get("playbooks", 0),
        members=record.get("members") or record.get("users_count", 1),
        cycle_started_at=_coerce_datetime(cycle_value),
    )


def _usage_to_record(usage: TenantUsage) -> dict:
    return {
        "projects": usage.projects,
        "playbooks": usage.playbooks,
        "members": usage.members,
        "cycle_started_at": usage.cycle_started_at.isoformat(),
    }


def _save_tenant_usage(tenant: Tenant) -> None:
    """Persist tenant usage counters."""
    with _write_cursor() as cur:
        cur.execute(
            """
            UPDATE tenants.tenants
               SET usage = %s,
                   updated_at = %s
             WHERE tenant_id = %s
            """,
            [Json(_usage_to_record(tenant.usage)), tenant.updated_at, tenant.tenant_id],
        )


@contextmanager
def _read_cursor(dict_cursor: bool = True):
    with _backend.get_connection() as conn:
        cursor_kwargs = {"cursor_factory": RealDictCursor} if dict_cursor else {}
        with conn.cursor(**cursor_kwargs) as cur:
            yield cur


@contextmanager
def _write_cursor(dict_cursor: bool = True):
    with _backend.get_connection() as conn:
        cursor_kwargs = {"cursor_factory": RealDictCursor} if dict_cursor else {}
        try:
            with conn.cursor(**cursor_kwargs) as cur:
                yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def _fetch_one(sql: str, params: Optional[Iterable[Any]] = None) -> Optional[dict]:
    with _read_cursor() as cur:
        cur.execute(sql, params or [])
        row = cur.fetchone()
    return dict(row) if row else None


def _fetch_all(sql: str, params: Optional[Iterable[Any]] = None) -> list[dict]:
    with _read_cursor() as cur:
        cur.execute(sql, params or [])
        rows = cur.fetchall()
    return [dict(row) for row in rows]


def _tenant_from_doc(record: dict) -> Tenant:
    return Tenant(
        tenant_id=record["tenant_id"],
        name=record["name"],
        owner_email=record["owner_email"],
        plan_tier=_plan_from_db(record.get("plan_tier")),
        status=record.get("status", "active"),
        api_token=record["api_token"],
        created_at=_coerce_datetime(record.get("created_at")),
        updated_at=_coerce_datetime(record.get("updated_at")),
        metadata=record.get("metadata") or {},
        usage=_usage_from_record(record.get("usage")),
    )


def _project_from_doc(document: dict) -> Project:
    return Project(
        tenant_id=document["tenant_id"],
        project_id=document["project_id"],
        name=document["name"],
        description=document.get("description"),
        created_at=_coerce_datetime(document.get("created_at")),
        updated_at=_coerce_datetime(document.get("updated_at")),
    )


def register_tenant(name: str, owner_email: str, plan_tier: PlanTier, metadata: Optional[dict] = None) -> Tenant:
    metadata = metadata or {}
    tenant_id = f"{_slugify_name(name)}-{uuid.uuid4().hex[:6]}"
    api_token = f"key-{secrets.token_urlsafe(16)}"
    now = _now()
    usage = TenantUsage()
    with _write_cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenants.tenants (
                tenant_id, name, owner_email, plan_tier, api_token,
                status, created_at, updated_at, metadata, usage
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
            """,
            [
                tenant_id,
                name,
                owner_email.lower(),
                _plan_to_db(plan_tier),
                api_token,
                "active",
                now,
                now,
                Json(metadata),
                Json(_usage_to_record(usage)),
            ],
        )
        row = cur.fetchone()
    if not row:
        raise RuntimeError("Failed to insert tenant record")
    return _tenant_from_doc(dict(row))


def get_tenant(tenant_id: str) -> Optional[Tenant]:
    row = _fetch_one("SELECT * FROM tenants.tenants WHERE tenant_id = %s", [tenant_id])
    if not row:
        return None
    return _tenant_from_doc(row)


def get_tenant_by_token(api_token: str) -> Optional[Tenant]:
    row = _fetch_one("SELECT * FROM tenants.tenants WHERE api_token = %s", [api_token])
    if not row:
        return None
    return _tenant_from_doc(row)


def update_tenant_plan(tenant_id: str, plan_tier: PlanTier) -> Tenant:
    now = _now()
    with _write_cursor() as cur:
        cur.execute(
            """
            UPDATE tenants.tenants
               SET plan_tier = %s,
                   updated_at = %s
             WHERE tenant_id = %s
            RETURNING *
            """,
            [_plan_to_db(plan_tier), now, tenant_id],
        )
        row = cur.fetchone()
    if not row:
        raise ValueError(f"Tenant {tenant_id} not found")
    return _tenant_from_doc(dict(row))


def _count_projects(tenant_id: str) -> int:
    row = _fetch_one("SELECT COUNT(*) AS total FROM tenants.projects WHERE tenant_id = %s", [tenant_id])
    return int(row["total"]) if row else 0


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
    with _write_cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenants.projects (
                project_id, tenant_id, name, description,
                created_at, updated_at
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            [
                project.project_id,
                project.tenant_id,
                project.name,
                project.description,
                project.created_at,
                project.updated_at,
            ],
        )
    tenant.usage.projects = current_project_count + 1
    tenant.updated_at = _now()
    _save_tenant_usage(tenant)
    return project


def list_projects(tenant_id: str) -> List[Project]:
    rows = _fetch_all(
        """
        SELECT project_id, tenant_id, name, description, created_at, updated_at
          FROM tenants.projects
         WHERE tenant_id = %s
         ORDER BY created_at DESC
        """,
        [tenant_id],
    )
    return [_project_from_doc(row) for row in rows]


def record_playbook_usage(tenant_id: str, increment: int = 1) -> Tenant:
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise ValueError("Tenant not found")
    plan = get_plan(tenant.plan_tier)
    if tenant.usage.playbooks + increment > plan.limits.max_playbooks:
        raise SubscriptionLimitError("Playbook storage limit reached for current plan.")
    tenant.usage.playbooks += increment
    tenant.updated_at = _now()
    _save_tenant_usage(tenant)
    return tenant


# ---- User management ---------------------------------------------------------------------------


def _user_from_doc(document: dict) -> AccountUser:
    return AccountUser(
        user_id=document["user_id"],
        tenant_id=document["tenant_id"],
        email=document["email"],
        full_name=document["full_name"],
        password_hash=document["password_hash"],
        created_at=_coerce_datetime(document.get("created_at")),
        updated_at=_coerce_datetime(document.get("updated_at")),
        roles=document.get("roles", ["member"]),
        oauth_provider=document.get("oauth_provider"),
        oauth_provider_id=document.get("oauth_provider_id"),
        picture_url=document.get("picture_url"),
    )


def register_user(tenant_id: str, email: str, full_name: str, password: str) -> AccountUser:
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise ValueError("Tenant not found")

    existing = _fetch_one(
        "SELECT user_id FROM tenants.users WHERE tenant_id = %s AND email = %s",
        [tenant_id, email.lower()],
    )
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
    with _write_cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenants.users (
                user_id, tenant_id, email, full_name, password_hash,
                roles, status, created_at, updated_at, metadata
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            [
                user.user_id,
                user.tenant_id,
                user.email,
                user.full_name,
                user.password_hash,
                user.roles,
                "active",
                user.created_at,
                user.updated_at,
                Json({}),
            ],
        )
    tenant.usage.members += 1
    tenant.updated_at = _now()
    _save_tenant_usage(tenant)
    return user


def get_user_by_email(tenant_id: str, email: str) -> Optional[AccountUser]:
    document = _fetch_one(
        """
        SELECT *
          FROM tenants.users
         WHERE tenant_id = %s AND email = %s
        """,
        [tenant_id, email.lower()],
    )
    if not document:
        return None
    return _user_from_doc(document)


def get_user(user_id: str) -> Optional[AccountUser]:
    document = _fetch_one("SELECT * FROM tenants.users WHERE user_id = %s", [user_id])
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
    row = _fetch_one("SELECT COUNT(*) AS total FROM tenants.users WHERE tenant_id = %s", [tenant_id])
    return int(row["total"]) if row else 0


def find_tenants_for_email(email: str) -> list[str]:
    """
    Find all tenant IDs where a user with the given email exists.
    Returns a list of tenant IDs.
    """
    rows = _fetch_all(
        "SELECT DISTINCT tenant_id FROM tenants.users WHERE email = %s",
        [email.lower()],
    )
    return [row["tenant_id"] for row in rows]


def update_user_password(user_id: str, password: str) -> AccountUser:
    user = get_user(user_id)
    if user is None:
        raise ValueError("User not found")
    salt, password_hash = _generate_password_hash(password)
    user.password_hash = f"{salt}:{password_hash}"
    user.updated_at = _now()
    with _write_cursor() as cur:
        cur.execute(
            """
            UPDATE tenants.users
               SET password_hash = %s,
                   updated_at = %s
             WHERE user_id = %s
            """,
            [user.password_hash, user.updated_at, user.user_id],
        )
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
    rows = _fetch_all(
        """
        SELECT token_id, tenant_id, user_id, name, secret_hash, created_at
          FROM tenants.api_tokens
         WHERE tenant_id = %s AND user_id = %s
         ORDER BY created_at DESC
        """,
        [tenant_id, user_id],
    )
    return [_token_from_doc(row) for row in rows]


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
    with _write_cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenants.api_tokens (
                token_id, tenant_id, user_id, name, secret_hash, created_at
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            [
                record.token_id,
                record.tenant_id,
                record.user_id,
                record.name,
                record.secret_hash,
                record.created_at,
            ],
        )
    return token_secret, record


def delete_api_token(token_id: str, tenant_id: str, user_id: str) -> bool:
    with _write_cursor(dict_cursor=False) as cur:
        cur.execute(
            """
            DELETE FROM tenants.api_tokens
             WHERE token_id = %s AND tenant_id = %s AND user_id = %s
            """,
            [token_id, tenant_id, user_id],
        )
        return cur.rowcount > 0


def get_api_token(secret: str) -> Optional[ApiTokenRecord]:
    hashed = _hash_secret(secret)
    document = _fetch_one(
        "SELECT * FROM tenants.api_tokens WHERE secret_hash = %s",
        [hashed],
    )
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
    with _write_cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenants.invitations (
                invite_id, tenant_id, inviter_user_id, invitee_email,
                status, created_at, expires_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            [
                invite.invite_id,
                invite.tenant_id,
                invite.inviter_user_id,
                invite.invitee_email,
                invite.status,
                invite.created_at,
                invite.expires_at,
            ],
        )
    return invite


def get_invitation(invite_id: str) -> Optional[Invitation]:
    document = _fetch_one(
        "SELECT * FROM tenants.invitations WHERE invite_id = %s",
        [invite_id],
    )
    if not document:
        return None
    return _invitation_from_doc(document)


def list_invitations(tenant_id: str, status: Optional[str] = None) -> List[Invitation]:
    """List invitations for a tenant, optionally filtered by status."""
    sql = "SELECT * FROM tenants.invitations WHERE tenant_id = %s"
    params: list[Any] = [tenant_id]
    if status:
        sql += " AND status = %s"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    rows = _fetch_all(sql, params)
    return [_invitation_from_doc(row) for row in rows]


def accept_invitation(invite_id: str) -> Invitation:
    """Mark invitation as accepted."""
    invite = get_invitation(invite_id)
    if not invite:
        raise ValueError("Invitation not found")
    if invite.status != "pending":
        raise ValueError(f"Invitation already {invite.status}")
    if _now() > invite.expires_at:
        invite.status = "expired"
        with _write_cursor() as cur:
            cur.execute(
                "UPDATE tenants.invitations SET status=%s WHERE invite_id=%s",
                [invite.status, invite.invite_id],
            )
        raise ValueError("Invitation expired")
    invite.status = "accepted"
    with _write_cursor() as cur:
        cur.execute(
            "UPDATE tenants.invitations SET status=%s WHERE invite_id=%s",
            [invite.status, invite.invite_id],
        )
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
    with _write_cursor() as cur:
        cur.execute(
            "UPDATE tenants.invitations SET status=%s WHERE invite_id=%s",
            [invite.status, invite.invite_id],
        )
    return invite


# ---- Admin & analytics ---------------------------------------------------------------------------


def list_all_tenants(limit: int = 100, skip: int = 0) -> List[Tenant]:
    """Admin only: list all tenants."""
    rows = _fetch_all(
        """
        SELECT * FROM tenants.tenants
        ORDER BY created_at DESC
        OFFSET %s LIMIT %s
        """,
        [skip, limit],
    )
    return [_tenant_from_doc(row) for row in rows]


def count_tenants() -> int:
    """Admin only: count all tenants."""
    row = _fetch_one("SELECT COUNT(*) AS total FROM tenants.tenants")
    return int(row["total"]) if row else 0


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
    with _write_cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenants.usage_events (
                event_id, tenant_id, user_id, event_type, payload, timestamp
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            [
                event.event_id,
                event.tenant_id,
                event.user_id,
                event.event_type,
                Json(event.payload),
                event.timestamp,
            ],
        )
    return event


def get_usage_summary(tenant_id: Optional[str] = None, days: int = 30) -> dict:
    """Admin analytics: usage summary."""
    cutoff = _now() - timedelta(days=days)
    sql = """
        SELECT event_type, COUNT(*) AS total
          FROM tenants.usage_events
         WHERE timestamp >= %s
    """
    params: list[Any] = [cutoff]
    if tenant_id:
        sql += " AND tenant_id = %s"
        params.append(tenant_id)
    sql += " GROUP BY event_type"
    rows = _fetch_all(sql, params)
    by_type = {row["event_type"]: int(row["total"]) for row in rows}
    total_events = sum(by_type.values())

    return {
        "period_days": days,
        "total_events": total_events,
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
    document = _fetch_one(
        """
        SELECT *
          FROM tenants.tenants
         WHERE owner_email = %s
           AND name ILIKE %s
        LIMIT 1
        """,
        [owner_email.lower(), name],
    )
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
        with _write_cursor() as cur:
            cur.execute(
                """
                UPDATE tenants.tenants
                   SET plan_tier = %s,
                       updated_at = %s
                 WHERE tenant_id = %s
                """,
                [_plan_to_db(tenant.plan_tier), tenant.updated_at, tenant.tenant_id],
            )
    return tenant


def find_expired_trials(plan_tier: PlanTier, cutoff: datetime) -> list[Tenant]:
    """Return tenants on a plan_tier whose created_at is older than cutoff and status=trial."""
    rows = _fetch_all(
        """
        SELECT *
          FROM tenants.tenants
         WHERE plan_tier = %s
           AND status = 'trial'
           AND created_at < %s
        """,
        [_plan_to_db(plan_tier), cutoff],
    )
    return [_tenant_from_doc(row) for row in rows]


# =====================================================================
# Verification Tokens (Email Signup Flow)
# =====================================================================

def create_verification_token(
    email: str,
    full_name: str,
    business_name: str,
    metadata: Optional[dict] = None,
    ttl_hours: int = 24
) -> str:
    """Create a verification token for email signup.
    
    Returns the token string to be sent to the user.
    """
    token = secrets.token_urlsafe(32)
    token_id = f"token-{uuid.uuid4().hex[:10]}"
    
    expires_at = _now() + timedelta(hours=ttl_hours)
    with _write_cursor() as cur:
        cur.execute(
            """
            INSERT INTO tenants.verification_tokens (
                token_id, token, email, full_name, business_name,
                metadata, expires_at, created_at, used
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            [
                token_id,
                token,
                email.lower(),
                full_name,
                business_name,
                Json(metadata or {}),
                expires_at,
                _now(),
                False,
            ],
        )
    return token


def verify_and_consume_token(token: str) -> Optional[dict]:
    """Verify token and mark as used.
    
    Returns token data if valid, None if invalid/expired/used.
    """
    with _write_cursor() as cur:
        cur.execute(
            """
            SELECT *
              FROM tenants.verification_tokens
             WHERE token = %s AND used = FALSE
             FOR UPDATE
            """,
            [token],
        )
        doc = cur.fetchone()
        if not doc:
            return None
        expires_at = _coerce_datetime(doc.get("expires_at"))
        # Normalize both datetimes to naive UTC for safe comparison
        now_ts = _now()
        from datetime import timezone as _dt_timezone
        if expires_at.tzinfo is not None and expires_at.utcoffset() is not None:
            expires_at_cmp = expires_at.astimezone(_dt_timezone.utc).replace(tzinfo=None)
        else:
            expires_at_cmp = expires_at
        if now_ts.tzinfo is not None and now_ts.utcoffset() is not None:
            now_cmp = now_ts.astimezone(_dt_timezone.utc).replace(tzinfo=None)
        else:
            now_cmp = now_ts
        if now_cmp > expires_at_cmp:
            return None
        cur.execute(
            """
            UPDATE tenants.verification_tokens
               SET used = TRUE,
                   used_at = %s
             WHERE token = %s
            """,
            [_now(), token],
        )
    return {
        "email": doc["email"],
        "full_name": doc["full_name"],
        "business_name": doc["business_name"],
        "metadata": doc.get("metadata", {}),
    }
