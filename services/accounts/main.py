from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from packages.accounts.models import PlanTier, SubscriptionPlan, Tenant, Project, AccountUser, ApiTokenRecord
from packages.accounts.repository import (
    list_plans,
    register_tenant,
    get_tenant,
    find_tenant_by_name_or_email,
    update_tenant_plan,
    create_project,
    list_projects,
    SubscriptionLimitError,
    register_user,
    authenticate_user,
    issue_jwt,
    list_api_tokens,
    create_api_token,
    delete_api_token,
    get_tenant_by_token,
    get_user,
    count_users_for_tenant,
    find_tenants_for_email,
    AuthenticationError,
    JWT_TTL_SECONDS,
)
from packages.accounts.oauth import oauth_service, OAuthProvider, OAuthUserInfo
from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging
from packages.kernel_common.mailer import Mailer
from packages.trust.onboarding import TenantOnboardingService

logger = configure_logging("accounts-service")
mailer = Mailer()

# Dev convenience: allow owner bootstrap login when no users exist (in-memory reset)
ALLOW_OWNER_BOOTSTRAP_LOGIN = os.getenv("ALLOW_OWNER_BOOTSTRAP_LOGIN", "1").lower() in {"1", "true", "yes"}

# Background task control
background_tasks_running = False
background_task_handle = None


async def trial_enforcement_job():
    """Background job to enforce trial expiration every 24 hours."""
    from packages.accounts.repository import TENANT_COLLECTION, PlanTier
    from datetime import datetime, timedelta
    
    while background_tasks_running:
        try:
            logger.info("Running trial enforcement job...")
            trial_days = 14
            cutoff_date = datetime.utcnow() - timedelta(days=trial_days)
            
            # Find silver tenants created more than trial_days ago with status=trial
            query = {
                "plan_tier": PlanTier.SILVER.value,
                "status": "trial",
                "created_at": {"$lt": cutoff_date}
            }
            
            downgraded_count = 0
            for doc in TENANT_COLLECTION.find(query):
                tenant_id = doc.get("tenant_id")
                try:
                    from packages.accounts.repository import enforce_trial_for_tenant
                    enforce_trial_for_tenant(tenant_id, trial_days=trial_days)
                    downgraded_count += 1
                    logger.info(f"Trial expired for tenant {tenant_id}, downgraded to free")
                except Exception as e:
                    logger.error(f"Failed to enforce trial for tenant {tenant_id}: {e}")
            
            if downgraded_count > 0:
                logger.info(f"Trial enforcement complete: {downgraded_count} tenants downgraded")
            else:
                logger.debug("Trial enforcement complete: no tenants to downgrade")
                
        except Exception as e:
            logger.error(f"Error in trial enforcement job: {e}")
        
        # Run every 24 hours
        await asyncio.sleep(86400)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage background tasks lifecycle."""
    global background_tasks_running, background_task_handle
    
    # Startup
    logger.info("Starting background tasks...")
    background_tasks_running = True
    background_task_handle = asyncio.create_task(trial_enforcement_job())
    
    yield
    
    # Shutdown
    logger.info("Stopping background tasks...")
    background_tasks_running = False
    if background_task_handle:
        background_task_handle.cancel()
        try:
            await background_task_handle
        except asyncio.CancelledError:
            pass

# Initialize onboarding service for Keycloak tenant provisioning
# Keycloak is optional - the service will gracefully fall back if not configured
keycloak_credentials = {
    "server_url": os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080"),
    "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli"),
    "client_secret": os.getenv("KEYCLOAK_CLIENT_SECRET"),
    "username": os.getenv("KEYCLOAK_USERNAME"),
    "password": os.getenv("KEYCLOAK_PASSWORD"),
}

# Log effective Keycloak configuration (without secrets)
try:
    _url = keycloak_credentials["server_url"]
    _scheme = "https" if _url.lower().startswith("https") else "http"
    _mode = (
        "client-secret"
        if keycloak_credentials.get("client_secret")
        else ("password" if keycloak_credentials.get("username") and keycloak_credentials.get("password") else "disabled")
    )
    logger.info(f"Keycloak config: url={_url} scheme={_scheme} auth={_mode}")
except Exception:
    pass

# Only attempt to initialize Keycloak if credentials are provided
if keycloak_credentials.get("client_secret") or (
    keycloak_credentials.get("username") and keycloak_credentials.get("password")
):
    logger.info("Initialising Keycloak onboarding service…")
    onboarding_service = TenantOnboardingService(
        server_url=keycloak_credentials["server_url"],
        client_id=keycloak_credentials["client_id"],
        client_secret=keycloak_credentials.get("client_secret"),
        username=keycloak_credentials.get("username"),
        password=keycloak_credentials.get("password"),
    )
else:
    logger.info("Keycloak credentials not configured. Proceeding with database-only tenant creation.")
    onboarding_service = TenantOnboardingService()  # Falls back gracefully


app = FastAPI(
    title="Dyocense Accounts Service",
    version="0.1.0",
    description="Tenant subscriptions, project catalogues, and plan management.",
    lifespan=lifespan,
)


class PlanResponse(BaseModel):
    tier: PlanTier
    name: str
    price_per_month: float
    description: str
    limits: dict
    features: list[str]

    @classmethod
    def from_model(cls, plan: SubscriptionPlan) -> "PlanResponse":
        return cls(
            tier=plan.tier,
            name=plan.name,
            price_per_month=plan.price_per_month,
            description=plan.description,
            limits=plan.limits.model_dump(),
            features=plan.features,
        )


class TenantRegistrationRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    owner_email: EmailStr
    plan_tier: PlanTier = PlanTier.FREE
    metadata: dict = Field(default_factory=dict)


class TenantRegistrationResponse(BaseModel):
    tenant_id: str
    api_token: str
    plan: PlanResponse
    already_exists: bool = False
    message: str | None = None


class OnboardingDetailsResponse(BaseModel):
    tenant_id: str
    keycloak_realm: str | None
    keycloak_url: str | None
    temporary_password: str | None
    username: str | None
    email: str
    login_url: str | None
    status: str = "ready"
    message: str | None = None


class TenantProfileResponse(BaseModel):
    tenant_id: str
    name: str
    owner_email: EmailStr
    plan: PlanResponse
    status: str
    usage: dict

    @classmethod
    def from_model(cls, tenant: Tenant) -> "TenantProfileResponse":
        plans = list_plans()
        matched_plan = next((p for p in plans if p.tier == tenant.plan_tier), plans[0])
        plan = PlanResponse.from_model(matched_plan)
        return cls(
            tenant_id=tenant.tenant_id,
            name=tenant.name,
            owner_email=tenant.owner_email,
            plan=plan,
            status=tenant.status,
            usage={
                "projects": tenant.usage.projects,
                "playbooks": tenant.usage.playbooks,
                "members": tenant.usage.members,
                "cycle_started_at": tenant.usage.cycle_started_at.isoformat(),
            },
        )


class SubscriptionUpdateRequest(BaseModel):
    plan_tier: PlanTier


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=400)


class ProjectResponse(BaseModel):
    project_id: str
    name: str
    description: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, project: Project) -> "ProjectResponse":
        return cls(
            project_id=project.project_id,
            name=project.name,
            description=project.description,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat(),
        )


class UserRegistrationRequest(BaseModel):
    tenant_id: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=120)
    password: str = Field(..., min_length=8, max_length=128)
    # Optional: legacy + keycloak flow
    temporary_password: str | None = Field(
        default=None, description="Temporary password from welcome email (optional in dev/legacy)."
    )
    # Backward compatibility: tests previously sent access_token here
    access_token: str | None = Field(
        default=None, description="Legacy field: tenant API token accepted for first user registration."
    )


class UserLoginRequest(BaseModel):
    tenant_id: str
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    token: str
    user_id: str
    tenant_id: str
    expires_in: int


class UserProfileResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: EmailStr
    full_name: str
    roles: list[str]

    @classmethod
    def from_model(cls, user: AccountUser) -> "UserProfileResponse":
        return cls(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            email=user.email,
            full_name=user.full_name,
            roles=user.roles,
        )


class ApiTokenResponse(BaseModel):
    token_id: str
    name: str
    created_at: str

    @classmethod
    def from_model(cls, record: ApiTokenRecord) -> "ApiTokenResponse":
        return cls(token_id=record.token_id, name=record.name, created_at=record.created_at.isoformat())


class ApiTokenCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)


class ApiTokenCreateResponse(ApiTokenResponse):
    secret: str


@app.get("/health", tags=["system"])
def health_check() -> dict:
    """Service health check with background job status."""
    return {
        "status": "healthy",
        "service": "accounts",
        "background_jobs": {
            "trial_enforcement": {
                "running": background_tasks_running,
                "enabled": True,
                "interval": "24 hours"
            }
        }
    }


@app.get("/v1/plans", response_model=list[PlanResponse], tags=["plans"])
def list_subscription_plans() -> list[PlanResponse]:
    return [PlanResponse.from_model(plan) for plan in list_plans()]


@app.post("/v1/tenants/register", response_model=TenantRegistrationResponse, status_code=status.HTTP_201_CREATED, tags=["tenants"])
def register_new_tenant(payload: TenantRegistrationRequest) -> TenantRegistrationResponse:
    # Check if this exact organization (name + owner email) already exists
    # This prevents the same person from accidentally registering the same org twice
    existing_tenant = find_tenant_by_name_or_email(
        name=payload.name,
        owner_email=payload.owner_email
    )
    
    if existing_tenant:
        # Tenant already exists - return existing tenant info
        logger.info(f"Found existing tenant {existing_tenant.tenant_id} for name '{payload.name}' and email '{payload.owner_email}'")
        plan = next(p for p in list_plans() if p.tier == existing_tenant.plan_tier)
        
        return TenantRegistrationResponse(
            tenant_id=existing_tenant.tenant_id,
            api_token=existing_tenant.api_token,
            plan=PlanResponse.from_model(plan),
            already_exists=True,
            message=f"You already registered the organization '{existing_tenant.name}'. Use the existing tenant ID to continue."
        )
    
    # No existing tenant found - create a new one
    tenant = register_tenant(
        name=payload.name,
        owner_email=payload.owner_email,
        plan_tier=payload.plan_tier,
        metadata=payload.metadata,
    )
    plan = next(p for p in list_plans() if p.tier == tenant.plan_tier)
    
    # Attempt Keycloak onboarding (non-blocking; continues if Keycloak unavailable)
    try:
        onboarding_result = onboarding_service.onboard_tenant(
            tenant_id=tenant.tenant_id,
            tenant_name=payload.name,
            owner_email=payload.owner_email,
        )
        logger.info(f"Tenant {tenant.tenant_id} onboarded to Keycloak: {onboarding_result}")
    # Store Keycloak realm info in tenant metadata
        tenant.metadata["keycloak_realm"] = onboarding_result.get("realm_id")
        tenant.metadata["keycloak_user_id"] = onboarding_result.get("user_id")
        tenant.metadata["temporary_password"] = onboarding_result.get("temporary_password")
    except Exception as e:
        logger.warning(f"Keycloak onboarding failed for tenant {tenant.tenant_id}: {e}. Continuing with fallback auth.")
    
    # Send onboarding email
    try:
        temp_pass = tenant.metadata.get("temporary_password")
        login_url = f"{os.getenv('APP_BASE_URL', 'http://localhost:5173')}/login?tenant={tenant.tenant_id}&email={payload.owner_email}&register=true"
        subject = f"Welcome to Dyocense - {payload.name}"
        text = (
            f"Hi,\n\n"
            f"Welcome to Dyocense! Your organization '{payload.name}' is now registered.\n\n"
            f"Tenant ID: {tenant.tenant_id}\n"
        )
        if temp_pass:
            text += f"Temporary Password: {temp_pass}\n"
        text += (
            f"\nClick here to create your account: {login_url}\n\n"
            f"You'll need to:\n"
            f"1. Enter your full name\n"
            f"2. Create a permanent password\n"
            f"3. Then you can sign in and start using Dyocense\n\n"
            f"Thank you,\nThe Dyocense Team"
        )
        mailer.send(payload.owner_email, subject, text)
    except Exception as e:
        logger.warning(f"Failed to send onboarding email to {payload.owner_email}: {e}")
    
    logger.info("Registered tenant %s on plan %s", tenant.tenant_id, tenant.plan_tier)
    return TenantRegistrationResponse(
        tenant_id=tenant.tenant_id,
        api_token=tenant.api_token,
        plan=PlanResponse.from_model(plan),
        already_exists=False,
        message="New organization created successfully."
    )


@app.get("/v1/tenants/me", response_model=TenantProfileResponse, tags=["tenants"])
def get_tenant_profile(identity: dict = Depends(require_auth)) -> TenantProfileResponse:
    tenant = get_tenant(identity["tenant_id"])
    if tenant is None:
        # Return a demo/fallback tenant when database is unavailable
        from packages.accounts.models import Tenant, TenantUsage, PlanTier
        from datetime import datetime

        now = datetime.utcnow()
        # Use a DNS-valid example domain to satisfy email-validator (avoid .local which is reserved)
        owner_email = identity.get("email") or "owner@example.com"
        tenant = Tenant(
            tenant_id=identity["tenant_id"],
            name="Demo Business",
            owner_email=owner_email,
            created_at=now,
            updated_at=now,
            status="active",
            plan_tier=PlanTier.FREE,
            usage=TenantUsage(
                projects=0,
                playbooks=0,
                members=1,
                cycle_started_at=now,
            ),
            api_token="demo-token",
            metadata={}
        )
    return TenantProfileResponse.from_model(tenant)


@app.put("/v1/tenants/me/profile", response_model=dict, tags=["tenants"])
def update_tenant_business_profile(payload: dict, identity: dict = Depends(require_auth)) -> dict:
    """
    Update tenant business profile metadata.
    Stores information like industry, company size, primary goals.
    """
    from packages.accounts.repository import TENANT_COLLECTION
    
    tenant_id = identity["tenant_id"]
    tenant = get_tenant(tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    # Extract business profile fields
    business_profile = {
        "industry": payload.get("industry"),
        "company_size": payload.get("company_size"),
        "team_size": payload.get("team_size"),
        "primary_goal": payload.get("primary_goal"),
        "business_type": payload.get("business_type"),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Remove None values
    business_profile = {k: v for k, v in business_profile.items() if v is not None}
    
    # Update tenant metadata
    result = TENANT_COLLECTION.update_one(
        {"tenant_id": tenant_id},
        {"$set": {"metadata.business_profile": business_profile}}
    )
    
    if result.modified_count == 0 and result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    logger.info(f"Updated business profile for tenant {tenant_id}")
    return {"message": "Business profile updated successfully", "profile": business_profile}


@app.get("/v1/goals/recommendations", response_model=dict, tags=["recommendations"])
def get_goal_recommendations(identity: dict = Depends(require_auth)) -> dict:
    """
    Get recommended playbook templates based on tenant's business profile.
    """
    tenant = get_tenant(identity["tenant_id"])
    # Graceful fallback: if tenant doesn't exist (e.g., anonymous/dev), use defaults
    if tenant is None:
        business_profile = {}
    else:
        # Get business profile from tenant metadata
        business_profile = tenant.metadata.get("business_profile", {})
    industry = business_profile.get("industry", "general")
    
    # Define recommendations based on industry
    recommendations_by_industry = {
        "retail": [
            {
                "id": "inventory_optimization",
                "title": "Inventory Optimization",
                "description": "Minimize holding costs while maintaining service levels across stores",
                "template_id": "inventory_basic",
                "archetype_id": "inventory_basic",  # Backward compatibility
                "icon": "📦",
                "estimated_time": "5 minutes",
                "tags": ["Popular", "Quick Start"]
            },
            {
                "id": "demand_forecasting",
                "title": "Demand Forecasting",
                "description": "Predict customer demand for better stock planning",
                "template_id": "forecasting_basic",
                "archetype_id": "forecasting_basic",  # Backward compatibility
                "icon": "📈",
                "estimated_time": "7 minutes",
                "tags": ["Recommended"]
            },
            {
                "id": "markdown_optimization",
                "title": "Markdown Optimization",
                "description": "Optimize pricing to clear seasonal inventory profitably",
                "template_id": "markdown_planner",
                "archetype_id": "markdown_planner",  # Backward compatibility
                "icon": "💰",
                "estimated_time": "10 minutes",
                "tags": ["Advanced"]
            }
        ],
        "manufacturing": [
            {
                "id": "production_planning",
                "title": "Production Planning",
                "description": "Optimize production schedules and resource allocation",
                "template_id": "production_scheduler",
                "archetype_id": "production_scheduler",  # Backward compatibility
                "icon": "🏭",
                "estimated_time": "8 minutes",
                "tags": ["Popular"]
            },
            {
                "id": "inventory_optimization",
                "title": "Raw Materials Inventory",
                "description": "Balance raw material costs with production needs",
                "template_id": "inventory_basic",
                "archetype_id": "inventory_basic",  # Backward compatibility
                "icon": "📦",
                "estimated_time": "5 minutes",
                "tags": ["Quick Start"]
            },
            {
                "id": "workforce_planning",
                "title": "Workforce Planning",
                "description": "Optimize shift schedules and staffing levels",
                "template_id": "staffing_basic",
                "archetype_id": "staffing_basic",  # Backward compatibility
                "icon": "👥",
                "estimated_time": "7 minutes",
                "tags": ["Recommended"]
            }
        ],
        "cpg": [
            {
                "id": "demand_forecasting",
                "title": "Demand Forecasting",
                "description": "Predict retailer orders and consumer demand",
                "template_id": "forecasting_basic",
                "archetype_id": "forecasting_basic",  # Backward compatibility
                "icon": "📈",
                "estimated_time": "7 minutes",
                "tags": ["Popular", "Quick Start"]
            },
            {
                "id": "inventory_optimization",
                "title": "Distribution Inventory",
                "description": "Optimize inventory across distribution centers",
                "archetype_id": "inventory_basic",
                "icon": "📦",
                "estimated_time": "5 minutes",
                "tags": ["Recommended"]
            },
            {
                "id": "promotion_planning",
                "title": "Promotion Planning",
                "description": "Optimize promotional strategies and trade spend",
                "archetype_id": "promotion_planner",
                "icon": "🎯",
                "estimated_time": "10 minutes",
                "tags": ["Advanced"]
            }
        ],
        "logistics": [
            {
                "id": "route_optimization",
                "title": "Route Optimization",
                "description": "Minimize delivery costs and improve service times",
                "archetype_id": "route_optimizer",
                "icon": "🚚",
                "estimated_time": "10 minutes",
                "tags": ["Popular"]
            },
            {
                "id": "warehouse_optimization",
                "title": "Warehouse Optimization",
                "description": "Optimize warehouse layout and picking strategies",
                "archetype_id": "warehouse_planner",
                "icon": "🏢",
                "estimated_time": "8 minutes",
                "tags": ["Recommended"]
            },
            {
                "id": "demand_forecasting",
                "title": "Volume Forecasting",
                "description": "Predict shipping volumes for capacity planning",
                "archetype_id": "forecasting_basic",
                "icon": "📈",
                "estimated_time": "7 minutes",
                "tags": ["Quick Start"]
            }
        ]
    }
    
    # Default recommendations for unknown industries
    default_recommendations = [
        {
            "id": "inventory_optimization",
            "title": "Inventory Optimization",
            "description": "Minimize holding costs while maintaining service levels",
            "archetype_id": "inventory_basic",
            "icon": "📦",
            "estimated_time": "5 minutes",
            "tags": ["Popular", "Quick Start"]
        },
        {
            "id": "demand_forecasting",
            "title": "Demand Forecasting",
            "description": "Predict future demand for better planning",
            "archetype_id": "forecasting_basic",
            "icon": "📈",
            "estimated_time": "7 minutes",
            "tags": ["Recommended"]
        },
        {
            "id": "workforce_planning",
            "title": "Workforce Planning",
            "description": "Optimize staffing schedules and labor costs",
            "archetype_id": "staffing_basic",
            "icon": "👥",
            "estimated_time": "7 minutes",
            "tags": ["Quick Start"]
        }
    ]
    
    recommendations = recommendations_by_industry.get(industry, default_recommendations)
    
    return {
        "recommendations": recommendations,
        "industry": industry,
        "message": f"Showing {len(recommendations)} recommended playbooks for {industry} industry"
    }


@app.put("/v1/tenants/me/subscription", response_model=TenantProfileResponse, tags=["tenants"])
def update_subscription(payload: SubscriptionUpdateRequest, identity: dict = Depends(require_auth)) -> TenantProfileResponse:
    try:
        tenant = update_tenant_plan(identity["tenant_id"], payload.plan_tier)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    logger.info("Tenant %s moved to %s plan", tenant.tenant_id, tenant.plan_tier)
    return TenantProfileResponse.from_model(tenant)


@app.get("/v1/tenants/me/api-token", response_model=dict, tags=["tenants"])
def get_tenant_api_token(identity: dict = Depends(require_auth)) -> dict:
    """
    Get the tenant's API token.
    This should only be accessible to admin users after login.
    """
    tenant = get_tenant(identity["tenant_id"])
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    # In production, you might want to restrict this to admin role only
    user_id = identity.get("subject")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User authentication required")
    
    return {
        "tenant_id": tenant.tenant_id,
        "api_token": tenant.api_token,
        "note": "Store this securely. Use it for programmatic API access."
    }


@app.post("/v1/tenants/me/api-token/rotate", response_model=dict, tags=["tenants"])
def rotate_tenant_api_token(identity: dict = Depends(require_auth)) -> dict:
    """
    Rotate the tenant's API token (generates a new one).
    This invalidates the old token immediately.
    """
    tenant = get_tenant(identity["tenant_id"])
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    # Verify user is authenticated (not API token access)
    user_id = identity.get("subject")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User authentication required")
    
    # Generate new API token
    import secrets
    new_token = f"key-{secrets.token_urlsafe(22)}"
    tenant.api_token = new_token
    
    # In production, persist this change to database
    from packages.accounts.repository import TENANT_COLLECTION, _tenant_to_doc
    if TENANT_COLLECTION is not None:
        TENANT_COLLECTION.update_one(
            {"tenant_id": tenant.tenant_id},
            {"$set": {"api_token": new_token}}
        )
    
    logger.info("Rotated API token for tenant %s by user %s", tenant.tenant_id, user_id)
    
    return {
        "tenant_id": tenant.tenant_id,
        "api_token": new_token,
        "note": "Old token has been invalidated. Update your applications with this new token."
    }


@app.get("/v1/tenants/me/onboarding", response_model=OnboardingDetailsResponse, tags=["tenants"])
def get_onboarding_details(identity: dict = Depends(require_auth)) -> OnboardingDetailsResponse:
    """Get Keycloak onboarding details for a tenant (login credentials, realm info, etc)."""
    tenant = get_tenant(identity["tenant_id"])
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    keycloak_realm = tenant.metadata.get("keycloak_realm")
    temp_password = tenant.metadata.get("temporary_password")
    username = tenant.owner_email.split("@")[0]
    
    return OnboardingDetailsResponse(
        tenant_id=tenant.tenant_id,
        keycloak_realm=keycloak_realm,
        keycloak_url=onboarding_service.keycloak.server_url if onboarding_service.keycloak else None,
        temporary_password=temp_password,
        username=username,
        email=tenant.owner_email,
        login_url=f"{onboarding_service.keycloak.server_url}/auth/realms/{keycloak_realm}/protocol/openid-connect/auth" if keycloak_realm and onboarding_service.keycloak else None,
        status="ready" if keycloak_realm else "pending_keycloak_setup",
        message="Use the temporary password to login. You'll be prompted to set a new password." if temp_password else None,
    )


@app.post("/v1/tenants/me/cancel", tags=["tenants"])
def cancel_subscription(identity: dict = Depends(require_auth)) -> dict:
    """Cancel subscription and deprovision Keycloak realm."""
    tenant = get_tenant(identity["tenant_id"])
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    
    try:
        # Attempt to deprovision Keycloak realm
        if onboarding_service.keycloak:
            onboarding_service.deprovisioning_tenant(tenant.tenant_id)
    except Exception as e:
        logger.warning(f"Keycloak deprovisioning failed for tenant {tenant.tenant_id}: {e}. Continuing with database cleanup.")
    
    # Update tenant status to cancelled
    from packages.accounts.repository import TENANT_COLLECTION, _tenant_to_doc
    TENANT_COLLECTION.update_one(
        {"tenant_id": tenant.tenant_id},
        {"$set": {"status": "cancelled", "updated_at": tenant.updated_at}}
    )
    
    logger.info(f"Tenant {tenant.tenant_id} subscription cancelled")
    return {
        "status": "cancelled",
        "tenant_id": tenant.tenant_id,
        "message": "Subscription cancelled. Your data will be retained for 30 days."
    }


@app.post("/v1/projects", response_model=ProjectResponse, tags=["projects"], status_code=status.HTTP_201_CREATED)
def create_new_project(payload: ProjectCreateRequest, identity: dict = Depends(require_auth)) -> ProjectResponse:
    try:
        project = create_project(identity["tenant_id"], payload.name, payload.description)
    except SubscriptionLimitError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return ProjectResponse.from_model(project)


@app.get("/v1/projects", response_model=list[ProjectResponse], tags=["projects"])
def list_tenant_projects(identity: dict = Depends(require_auth)) -> list[ProjectResponse]:
    return [ProjectResponse.from_model(project) for project in list_projects(identity["tenant_id"])]


@app.post("/v1/users/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
def register_new_user(payload: UserRegistrationRequest) -> UserProfileResponse:
    logger.info(f"Registration attempt for tenant={payload.tenant_id}, email={payload.email}")
    # Verify tenant exists and temporary password matches (or apply fallback)
    tenant = get_tenant(payload.tenant_id)
    if tenant is None:
        logger.warning(f"Registration failed: tenant {payload.tenant_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    
    # Verify temporary password from tenant metadata (set during Keycloak onboarding)
    stored_temp_pass = tenant.metadata.get("temporary_password")
    if stored_temp_pass:
        if payload.temporary_password is None or stored_temp_pass != payload.temporary_password:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid temporary password.")
    else:
        # Fallback: If no temporary password was issued (e.g., Keycloak unavailable),
        # allow the FIRST user to register if either:
        #  - they use the owner email, OR
        #  - they present the tenant API token via legacy access_token field
        try:
            user_count = count_users_for_tenant(tenant.tenant_id)
        except Exception:
            user_count = 0
        is_first_user = user_count == 0
        owner_email_ok = payload.email.lower() == tenant.owner_email.lower()
        api_token_ok = bool(payload.access_token) and payload.access_token == tenant.api_token
        if not (is_first_user and (owner_email_ok or api_token_ok)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Registration requires a temporary password or an invitation. "
                    "For first-time setup without Keycloak, use the owner email or provide the tenant API token."
                ),
            )
    
    try:
        user = register_user(payload.tenant_id, payload.email, payload.full_name, payload.password)
        logger.info(f"Registered user {user.user_id} ({user.email}) for tenant {user.tenant_id}")
        
        # Clear temporary password after successful registration (if present)
        if stored_temp_pass:
            tenant.metadata.pop("temporary_password", None)
            # Persist the metadata change if using a database
            try:
                from packages.accounts.repository import TENANT_COLLECTION, _tenant_to_doc
                TENANT_COLLECTION.replace_one({"tenant_id": tenant.tenant_id}, _tenant_to_doc(tenant), upsert=True)
            except Exception:
                pass
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    
    logger.info("Registered user %s for tenant %s", user.email, user.tenant_id)
    return UserProfileResponse.from_model(user)


@app.post("/v1/users/login", response_model=UserLoginResponse, tags=["users"])
def login_user(payload: UserLoginRequest) -> UserLoginResponse:
    logger.info(f"Login attempt for tenant={payload.tenant_id}, email={payload.email}")
    try:
        # Dev-only bootstrap: if no users exist (likely after in-memory reset) and email matches
        # the tenant owner, auto-register this user to avoid a dead-end in local dev.
        try:
            tenant = get_tenant(payload.tenant_id)
        except Exception:
            tenant = None
        if tenant and ALLOW_OWNER_BOOTSTRAP_LOGIN:
            try:
                user_count = count_users_for_tenant(tenant.tenant_id)
            except Exception:
                user_count = 0
            if user_count == 0 and payload.email.lower() == tenant.owner_email.lower():
                try:
                    # Derive a simple full name from email prefix
                    full_name = payload.email.split("@")[0].replace(".", " ").title()
                    register_user(tenant.tenant_id, payload.email, full_name, payload.password)
                    logger.info(
                        "Bootstrap-registered owner user %s for tenant %s during login",
                        payload.email,
                        tenant.tenant_id,
                    )
                except AuthenticationError:
                    # If user somehow exists concurrently, ignore and proceed to authenticate
                    pass

        user = authenticate_user(payload.tenant_id, payload.email, payload.password)
        logger.info(f"Login successful for user {user.user_id}")
        token = issue_jwt(user)
        return UserLoginResponse(
            token=token,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            expires_in=JWT_TTL_SECONDS,
        )
    except AuthenticationError as exc:
        logger.warning(f"Login failed for tenant={payload.tenant_id}, email={payload.email}: {exc}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.") from exc


# =====================================================================
# OAuth Social Login Endpoints (Google, Microsoft, Apple)
# =====================================================================

@app.get("/v1/auth/providers", response_model=dict, tags=["oauth"])
def get_oauth_providers() -> dict:
    """Get list of enabled OAuth providers for social login.
    
    Returns enabled providers (google, microsoft, apple) based on environment configuration.
    SMB-optimized: Only the most popular business authentication methods.
    """
    enabled = oauth_service.get_enabled_providers()
    
    provider_info = {
        "google": {
            "name": "Google",
            "description": "Sign in with Gmail or Google Workspace",
            "icon": "google",
            "color": "#4285F4"
        },
        "microsoft": {
            "name": "Microsoft",
            "description": "Sign in with Outlook or Microsoft 365",
            "icon": "microsoft",
            "color": "#00A4EF"
        },
        "apple": {
            "name": "Apple",
            "description": "Sign in with Apple ID",
            "icon": "apple",
            "color": "#000000"
        }
    }
    
    return {
        "enabled_providers": enabled,
        "providers": {p: provider_info[p] for p in enabled}
    }


@app.get("/v1/auth/{provider}/authorize", tags=["oauth"])
def oauth_authorize(provider: OAuthProvider, tenant_id: str | None = None) -> dict:
    """Initiate OAuth login flow for a provider.
    
    Args:
        provider: OAuth provider (google, microsoft, apple)
        tenant_id: Optional tenant ID for direct tenant login
        
    Returns:
        Authorization URL to redirect user to and state token for CSRF protection
    """
    if not oauth_service.is_enabled(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not configured"
        )
    
    # Generate state token with optional tenant_id
    import secrets
    import json
    import base64
    
    state_data = {"nonce": secrets.token_urlsafe(16)}
    if tenant_id:
        state_data["tenant_id"] = tenant_id
    
    state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
    
    auth_url = oauth_service.get_authorization_url(provider, state)
    
    return {
        "authorization_url": auth_url,
        "state": state,
        "provider": provider
    }


@app.post("/v1/auth/{provider}/callback", response_model=UserLoginResponse, tags=["oauth"])
async def oauth_callback(
    provider: OAuthProvider,
    code: str,
    state: str,
    tenant_id: str | None = None
) -> UserLoginResponse:
    """Handle OAuth callback and create/login user.
    
    Args:
        provider: OAuth provider
        code: Authorization code from provider
        state: State token for CSRF protection
        tenant_id: Optional tenant ID (can also be in state)
        
    Returns:
        JWT token and user information
    """
    if not oauth_service.is_enabled(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not configured"
        )
    
    try:
        # Decode state
        import json
        import base64
        state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
        
        # Get tenant_id from state or parameter
        if not tenant_id:
            tenant_id = state_data.get("tenant_id")
        
        # Exchange code for access token
        access_token = await oauth_service.exchange_code_for_token(provider, code)
        
        # Get user info from provider
        user_info: OAuthUserInfo = await oauth_service.get_user_info(provider, access_token)
        
        if not user_info.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by OAuth provider"
            )
        
        # Find or create user
        from packages.accounts.repository import USER_COLLECTION, _user_to_doc, _doc_to_user
        import uuid
        
        # Check if user exists with this OAuth provider
        user_doc = USER_COLLECTION.find_one({
            "oauth_provider": provider,
            "oauth_provider_id": user_info.provider_user_id
        }) if USER_COLLECTION else None
        
        if user_doc:
            # Existing OAuth user
            user = _doc_to_user(user_doc)
            logger.info(f"OAuth login: existing user {user.user_id} via {provider}")
        else:
            # Check if email exists (link OAuth to existing account)
            if tenant_id:
                user_doc = USER_COLLECTION.find_one({
                    "tenant_id": tenant_id,
                    "email": user_info.email
                }) if USER_COLLECTION else None
                
                if user_doc:
                    # Link OAuth to existing email account
                    USER_COLLECTION.update_one(
                        {"user_id": user_doc["user_id"]},
                        {"$set": {
                            "oauth_provider": provider,
                            "oauth_provider_id": user_info.provider_user_id,
                            "picture_url": user_info.picture
                        }}
                    )
                    user = _doc_to_user(user_doc)
                    logger.info(f"Linked OAuth {provider} to existing user {user.user_id}")
                else:
                    # Create new user in existing tenant
                    tenant = get_tenant(tenant_id)
                    if not tenant:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Tenant not found"
                        )
                    
                    user = AccountUser(
                        user_id=str(uuid.uuid4()),
                        tenant_id=tenant_id,
                        email=user_info.email,
                        full_name=user_info.full_name or user_info.email.split("@")[0],
                        password_hash="",  # No password for OAuth users
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        roles=["member"],
                        oauth_provider=provider,
                        oauth_provider_id=user_info.provider_user_id,
                        picture_url=user_info.picture
                    )
                    
                    if USER_COLLECTION:
                        USER_COLLECTION.insert_one(_user_to_doc(user))
                    
                    logger.info(f"Created new OAuth user {user.user_id} in tenant {tenant_id} via {provider}")
            else:
                # New user, no tenant - need to find or create tenant
                # Find tenants with this email
                tenant_ids = find_tenants_for_email(user_info.email)
                
                if tenant_ids:
                    # Use first tenant found
                    tenant_id = tenant_ids[0]
                    tenant = get_tenant(tenant_id)
                else:
                    # Create new tenant for this user
                    business_name = user_info.email.split("@")[0].replace(".", " ").title() + "'s Business"
                    tenant = register_tenant(
                        name=business_name,
                        owner_email=user_info.email,
                        plan_tier=PlanTier.FREE,
                        metadata={"signup_method": f"oauth_{provider}"}
                    )
                    tenant_id = tenant.tenant_id
                    logger.info(f"Created new tenant {tenant_id} for OAuth user via {provider}")
                
                # Create user in tenant
                user = AccountUser(
                    user_id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    email=user_info.email,
                    full_name=user_info.full_name or user_info.email.split("@")[0],
                    password_hash="",  # No password for OAuth users
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    roles=["owner"],  # First user is owner
                    oauth_provider=provider,
                    oauth_provider_id=user_info.provider_user_id,
                    picture_url=user_info.picture
                )
                
                if USER_COLLECTION:
                    USER_COLLECTION.insert_one(_user_to_doc(user))
                
                logger.info(f"Created new OAuth user {user.user_id} with new tenant {tenant_id} via {provider}")
        
        # Issue JWT token
        token = issue_jwt(user)
        
        return UserLoginResponse(
            token=token,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            expires_in=JWT_TTL_SECONDS,
        )
        
    except ValueError as exc:
        logger.error(f"OAuth callback error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(exc)}"
        ) from exc
    except Exception as exc:
        logger.error(f"Unexpected OAuth error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        ) from exc


@app.get("/v1/users/tenants", response_model=dict, tags=["users"])
def get_user_tenants(email: str) -> dict:
    """
    Get list of tenants where a user with the given email exists.
    Returns tenant_id and name for each tenant.
    """
    try:
        # Validate email format
        if not email or "@" not in email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
        
        # Find all tenant IDs where this email exists
        tenant_ids = find_tenants_for_email(email)
        
        # Fetch tenant details for each
        tenants = []
        for tenant_id in tenant_ids:
            tenant = get_tenant(tenant_id)
            if tenant:
                tenants.append({
                    "tenant_id": tenant.tenant_id,
                    "name": tenant.name
                })
        
        logger.info(f"Found {len(tenants)} tenant(s) for email {email}")
        return {"tenants": tenants}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching tenants for email {email}: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch tenants") from exc


@app.get("/v1/users/me", response_model=UserProfileResponse, tags=["users"])
def get_current_user(identity: dict = Depends(require_auth)) -> UserProfileResponse:
    user_id = identity.get("subject")
    tenant_id = identity["tenant_id"]
    user = get_user(user_id) if user_id else None

    # Normal path: real user found and belongs to tenant
    if user and user.tenant_id == tenant_id:
        return UserProfileResponse.from_model(user)

    # Fallback for API-token, anonymous or bootstrap contexts where there is no per-user account yet.
    # Identity subject will often be 'api-key', 'anonymous', None or 'user' in these cases.
    if user_id in {"api-key", None, "user", "anonymous"}:
        tenant = get_tenant(tenant_id)
        if tenant:
            # Synthesize a virtual owner profile so the UI can proceed.
            return UserProfileResponse(
                user_id=f"tenant-owner-{tenant.tenant_id}",
                tenant_id=tenant.tenant_id,
                email=tenant.owner_email,
                full_name=tenant.name or "Tenant Owner",
                roles=["owner", "admin"],
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.get("/v1/users/api-tokens", response_model=list[ApiTokenResponse], tags=["users"])
def list_user_tokens(identity: dict = Depends(require_auth)) -> list[ApiTokenResponse]:
    user_id = identity.get("subject")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User context required.")
    records = list_api_tokens(identity["tenant_id"], user_id)
    return [ApiTokenResponse.from_model(record) for record in records]


@app.post("/v1/users/api-tokens", response_model=ApiTokenCreateResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user_token(payload: ApiTokenCreateRequest, identity: dict = Depends(require_auth)) -> ApiTokenResponse:
    user_id = identity.get("subject")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User context required.")
    secret, record = create_api_token(identity["tenant_id"], user_id, payload.name)
    logger.info("Issued API token %s for user %s tenant %s", record.token_id, user_id, identity["tenant_id"])
    return ApiTokenCreateResponse(
        token_id=record.token_id,
        name=record.name,
        created_at=record.created_at.isoformat(),
        secret=secret,
    )


@app.delete("/v1/users/api-tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
def delete_user_token(token_id: str, identity: dict = Depends(require_auth)):
    user_id = identity.get("subject")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User context required.")
    if not delete_api_token(token_id, identity["tenant_id"], user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")


# ---- Invitations --------------------------------------------------------------------------------


class InvitationCreateRequest(BaseModel):
    invitee_email: EmailStr


class InvitationResponse(BaseModel):
    invite_id: str
    tenant_id: str
    inviter_user_id: str
    invitee_email: str
    status: str
    created_at: str
    expires_at: str


@app.post("/v1/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED, tags=["invitations"])
def create_team_invitation(payload: InvitationCreateRequest, identity: dict = Depends(require_auth)) -> InvitationResponse:
    """Create a team invitation for new member."""
    user_id = identity.get("subject")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User context required.")

    from packages.accounts.repository import create_invitation
    invite = create_invitation(identity["tenant_id"], user_id, payload.invitee_email)

    # Send invitation email
    try:
        accept_url = f"{os.getenv('APP_BASE_URL', 'http://localhost:5173')}/accept-invite/{invite.invite_id}"
        subject = "You're invited to join a team on Dyocense"
        text = f"Hi,\n\nYou've been invited to join a team on Dyocense.\n\nAccept here: {accept_url}\n\nThis invitation expires on {invite.expires_at.isoformat()}."
        mailer.send(payload.invitee_email, subject, text)
    except Exception as e:
        logger.warning(f"Failed to send invitation email to {payload.invitee_email}: {e}")

    return InvitationResponse(
        invite_id=invite.invite_id,
        tenant_id=invite.tenant_id,
        inviter_user_id=invite.inviter_user_id,
        invitee_email=invite.invitee_email,
        status=invite.status,
        created_at=invite.created_at.isoformat(),
        expires_at=invite.expires_at.isoformat(),
    )


@app.get("/v1/invitations", response_model=list[InvitationResponse], tags=["invitations"])
def list_team_invitations(identity: dict = Depends(require_auth)) -> list[InvitationResponse]:
    """List all invitations for this tenant."""
    from packages.accounts.repository import list_invitations
    invites = list_invitations(identity["tenant_id"])
    return [
        InvitationResponse(
            invite_id=i.invite_id,
            tenant_id=i.tenant_id,
            inviter_user_id=i.inviter_user_id,
            invitee_email=i.invitee_email,
            status=i.status,
            created_at=i.created_at.isoformat(),
            expires_at=i.expires_at.isoformat(),
        )
        for i in invites
    ]


@app.post("/v1/invitations/{invite_id}/accept", tags=["invitations"])
def accept_team_invitation(invite_id: str) -> dict:
    """Public endpoint to accept an invitation (returns tenant info)."""
    from packages.accounts.repository import accept_invitation, get_tenant
    invite = accept_invitation(invite_id)
    tenant = get_tenant(invite.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return {
        "tenant_id": tenant.tenant_id,
        "tenant_name": tenant.name,
        "invitee_email": invite.invitee_email,
        "message": "Invitation accepted! You can now register with this tenant.",
    }


@app.delete("/v1/invitations/{invite_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["invitations"], response_model=None)
def revoke_team_invitation(invite_id: str, identity: dict = Depends(require_auth)):
    """Revoke a pending invitation."""
    from packages.accounts.repository import revoke_invitation
    try:
        revoke_invitation(invite_id, identity["tenant_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/v1/invitations/{invite_id}/resend", tags=["invitations"])
def resend_team_invitation(invite_id: str, identity: dict = Depends(require_auth)) -> dict:
    """Resend invitation email."""
    from packages.accounts.repository import get_invitation
    invite = get_invitation(invite_id)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
    if invite.tenant_id != identity["tenant_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if invite.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot resend {invite.status} invitation")
    
    # Resend email
    try:
        accept_url = f"{os.getenv('APP_BASE_URL', 'http://localhost:5173')}/accept-invite/{invite.invite_id}"
        subject = "Reminder: You're invited to join a team on Dyocense"
        text = f"Hi,\n\nYou've been invited to join a team on Dyocense.\n\nAccept here: {accept_url}\n\nThis invitation expires on {invite.expires_at.isoformat()}."
        mailer.send(invite.invitee_email, subject, text)
    except Exception as e:
        logger.warning(f"Failed to resend invitation email to {invite.invitee_email}: {e}")
    
    return {"message": f"Invitation resent to {invite.invitee_email}", "invite_id": invite.invite_id}


# ---- Trial & billing ----------------------------------------------------------------------------


@app.get("/v1/billing/portal", tags=["billing"])
def get_billing_portal(identity: dict = Depends(require_auth)) -> dict:
    """Placeholder billing portal link (e.g., Stripe)."""
    return {
        "portal_url": f"https://billing.dyocense.com?tenant={identity['tenant_id']}",
        "message": "Manage your subscription via the billing portal.",
    }


@app.post("/v1/trial/enforce", tags=["billing"])
def enforce_trial(identity: dict = Depends(require_auth)) -> dict:
    """Manually enforce trial downgrade for a tenant."""
    from packages.accounts.repository import enforce_trial_for_tenant
    tenant = enforce_trial_for_tenant(identity["tenant_id"])
    return {"tenant_id": tenant.tenant_id, "plan_tier": tenant.plan_tier.value, "status": tenant.status}


@app.post("/v1/trial/enforce-all", tags=["billing"])
def enforce_all_trials(identity: dict = Depends(require_auth)) -> dict:
    """Admin only: manually trigger trial enforcement for all expired trials."""
    from packages.accounts.repository import ADMIN_TENANT_ID, TENANT_COLLECTION, enforce_trial_for_tenant, PlanTier
    from datetime import datetime, timedelta
    
    if identity["tenant_id"] != ADMIN_TENANT_ID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    trial_days = 14
    cutoff_date = datetime.utcnow() - timedelta(days=trial_days)
    
    query = {
        "plan_tier": PlanTier.SILVER.value,
        "status": "trial",
        "created_at": {"$lt": cutoff_date}
    }
    
    downgraded = []
    errors = []
    
    for doc in TENANT_COLLECTION.find(query):
        tenant_id = doc.get("tenant_id")
        try:
            tenant = enforce_trial_for_tenant(tenant_id, trial_days=trial_days)
            downgraded.append({
                "tenant_id": tenant.tenant_id,
                "plan_tier": tenant.plan_tier.value,
                "status": tenant.status
            })
        except Exception as e:
            errors.append({"tenant_id": tenant_id, "error": str(e)})
    
    return {
        "message": f"Enforced {len(downgraded)} trial expirations",
        "downgraded": downgraded,
        "errors": errors
    }


# ---- Admin endpoints ----------------------------------------------------------------------------


@app.get("/v1/admin/tenants", tags=["admin"])
def list_all_tenants_admin(identity: dict = Depends(require_auth), limit: int = 100, skip: int = 0) -> dict:
    """Admin only: list all tenants."""
    from packages.accounts.repository import ADMIN_TENANT_ID, list_all_tenants, count_tenants
    if identity["tenant_id"] != ADMIN_TENANT_ID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    tenants = list_all_tenants(limit=limit, skip=skip)
    total = count_tenants()
    return {
        "tenants": [
            {
                "tenant_id": t.tenant_id,
                "name": t.name,
                "owner_email": t.owner_email,
                "plan_tier": t.plan_tier.value,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "usage": {
                    "projects": t.usage.projects,
                    "playbooks": t.usage.playbooks,
                    "members": t.usage.members,
                },
            }
            for t in tenants
        ],
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@app.put("/v1/admin/tenants/{tenant_id}/plan", tags=["admin"])
def update_tenant_plan_admin(tenant_id: str, plan_tier: PlanTier, identity: dict = Depends(require_auth)) -> dict:
    """Admin only: change tenant plan."""
    from packages.accounts.repository import ADMIN_TENANT_ID, update_tenant_plan
    if identity["tenant_id"] != ADMIN_TENANT_ID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    tenant = update_tenant_plan(tenant_id, plan_tier)
    return {"tenant_id": tenant.tenant_id, "plan_tier": tenant.plan_tier.value, "updated_at": tenant.updated_at.isoformat()}


@app.get("/v1/admin/analytics", tags=["admin"])
def get_analytics_summary(identity: dict = Depends(require_auth), days: int = 30) -> dict:
    """Admin only: usage analytics summary."""
    from packages.accounts.repository import ADMIN_TENANT_ID, get_usage_summary
    if identity["tenant_id"] != ADMIN_TENANT_ID:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return get_usage_summary(days=days)


# ---- Usage events -------------------------------------------------------------------------------


class AnalyticsEventRequest(BaseModel):
    event_type: str
    payload: dict = Field(default_factory=dict)


@app.post("/v1/analytics/events", status_code=status.HTTP_201_CREATED, tags=["analytics"])
def record_analytics_event(payload: AnalyticsEventRequest, identity: dict = Depends(require_auth)) -> dict:
    """Record a usage event for analytics."""
    from packages.accounts.repository import record_usage_event
    event = record_usage_event(
        tenant_id=identity["tenant_id"],
        event_type=payload.event_type,
        payload=payload.payload,
        user_id=identity.get("subject"),
    )
    return {"event_id": event.event_id, "timestamp": event.timestamp.isoformat()}


# ---- Connectors (stub implementation for unified mode) -----------------------------------------


class ConnectorResponse(BaseModel):
    """Connector response model."""
    connector_id: str
    tenant_id: str
    connector_type: str
    display_name: str
    status: str
    sync_frequency: str
    created_at: str
    updated_at: str


@app.get("/v1/connectors", response_model=list[ConnectorResponse], tags=["connectors"])
def list_connectors(identity: dict = Depends(require_auth)) -> list[ConnectorResponse]:
    """List connectors for the authenticated tenant.
    
    Note: This is a stub implementation for SMB/unified mode.
    Full connectors functionality requires the connectors microservice.
    """
    # Return empty list for now - connectors service is not enabled in unified/Postgres mode
    return []


@app.post("/v1/connectors", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED, tags=["connectors"])
def create_connector(identity: dict = Depends(require_auth)) -> ConnectorResponse:
    """Create a new connector.
    
    Note: This is a stub implementation for SMB/unified mode.
    Full connectors functionality requires the connectors microservice.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Connectors are not available in this deployment mode. Please upgrade to enable data connectors."
    )


@app.get("/v1/connectors/{connector_id}", response_model=ConnectorResponse, tags=["connectors"])
def get_connector(connector_id: str, identity: dict = Depends(require_auth)) -> ConnectorResponse:
    """Get a specific connector.
    
    Note: This is a stub implementation for SMB/unified mode.
    """
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")


@app.put("/v1/connectors/{connector_id}", response_model=ConnectorResponse, tags=["connectors"])
def update_connector(connector_id: str, identity: dict = Depends(require_auth)) -> ConnectorResponse:
    """Update a connector.
    
    Note: This is a stub implementation for SMB/unified mode.
    """
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")


@app.delete("/v1/connectors/{connector_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["connectors"])
def delete_connector(connector_id: str, identity: dict = Depends(require_auth)):
    """Delete a connector.
    
    Note: This is a stub implementation for SMB/unified mode.
    """
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")


@app.post("/v1/connectors/{connector_id}/test", tags=["connectors"])
def test_connector(connector_id: str, identity: dict = Depends(require_auth)) -> dict:
    """Test a connector connection.
    
    Note: This is a stub implementation for SMB/unified mode.
    """
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")


@app.post("/v1/connectors/test", tags=["connectors"])
def test_connector_config(identity: dict = Depends(require_auth)) -> dict:
    """Test a connector configuration without saving.
    
    Note: This is a stub implementation for SMB/unified mode.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Connectors are not available in this deployment mode."
    )


# ---- Runs (stub implementation for unified mode) -----------------------------------------------


class RunResponse(BaseModel):
    """Run response model."""
    run_id: str
    tenant_id: str
    project_id: str
    status: str
    created_at: str


class RunStatusResponse(BaseModel):
    """Detailed run status response."""
    run_id: str
    tenant_id: str
    project_id: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class RunListResponse(BaseModel):
    """List of runs."""
    runs: list[RunResponse]
    total: int


@app.get("/v1/accounts/runs", response_model=RunListResponse, tags=["accounts-runs"])
def list_runs(
    project_id: str | None = None,
    limit: int = 10,
    identity: dict = Depends(require_auth)
) -> RunListResponse:
    """List runs for the authenticated tenant.
    
    Note: This is a stub implementation for SMB/unified mode.
    Full runs/orchestration functionality is coming soon.
    """
    # Return empty list for now
    return RunListResponse(runs=[], total=0)


@app.post("/v1/accounts/runs", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED, tags=["accounts-runs"])
def create_run(identity: dict = Depends(require_auth)) -> RunResponse:
    """Create a new run.
    
    Note: This is a stub implementation for SMB/unified mode.
    Full runs/orchestration functionality is coming soon.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Runs are not fully implemented in this deployment mode yet."
    )


@app.get("/v1/accounts/runs/{run_id}", response_model=RunStatusResponse, tags=["accounts-runs"])
def get_run(run_id: str, identity: dict = Depends(require_auth)) -> RunStatusResponse:
    """Get a specific run.
    
    Note: This is a stub implementation for SMB/unified mode.
    """
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

