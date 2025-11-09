# Backend Integration Plan - Email Signup Flow

**Date**: November 9, 2025  
**Status**: IMPLEMENTATION READY

## Current Architecture Analysis

### ✅ What Exists

#### 1. **Database Layer** (MongoDB via `kernel_common.persistence`)

- **Collections**: `tenants`, `projects`, `tenant_users`, `user_tokens`, `invitations`, `usage_events`
- **Fallback**: In-memory collections when MongoDB disabled
- **Configuration**: Supports both MongoDB and PostgreSQL backends via `PERSISTENCE_BACKEND` env var

#### 2. **Accounts Service** (`services/accounts/main.py`)

- **OAuth Flow**: ✅ Fully implemented (`/v1/auth/providers`, authorize, callback)
- **User Registration**: ✅ `/v1/users/register` (requires tenant + temporary password)
- **User Login**: ✅ `/v1/users/login` (requires tenant_id + email + password)
- **Tenant Management**: ✅ `/v1/tenants/register`

#### 3. **Models** (`packages/accounts/models.py`)

- ✅ `Tenant` - Organization with plan tier, usage tracking
- ✅ `AccountUser` - User accounts with password hashing, OAuth support
- ✅ `Project` - Tenant workspaces/locations
- ✅ `ApiTokenRecord` - API keys
- ✅ `Invitation` - Team invites

#### 4. **Repository** (`packages/accounts/repository.py`)

- ✅ `register_tenant()` - Create tenant with API token
- ✅ `register_user()` - Create user with password hash
- ✅ `authenticate_user()` - Verify credentials
- ✅ `issue_jwt()` - Generate JWT tokens
- ✅ `create_project()` - Create workspace

### ❌ What's Missing

The frontend expects:

1. **`POST /v1/auth/signup`** - Single-step signup (email → create everything)
2. **`POST /v1/auth/verify`** - Magic link verification (token → JWT)

Current flow requires:

1. **Tenant registration** (`/v1/tenants/register`) → get tenant_id + api_token
2. **User registration** (`/v1/users/register`) → requires tenant_id + temporary_password
3. **User login** (`/v1/users/login`) → get JWT

**Gap**: No streamlined SMB signup flow with email verification.

## Implementation Plan

### Phase 1: Add Verification Token Model & Repository

#### Step 1.1: Add Model

**File**: `packages/accounts/models.py`

```python
class VerificationToken(BaseModel):
    """Email verification token for passwordless signup."""
    token_id: str
    email: str
    full_name: str
    business_name: str
    metadata: dict = Field(default_factory=dict)  # Store intent, use_case
    expires_at: datetime
    created_at: datetime
    used: bool = False
```

#### Step 1.2: Add Repository Functions

**File**: `packages/accounts/repository.py`

Add collection:

```python
VERIFICATION_TOKENS_COLLECTION = get_collection("verification_tokens")
```

Add functions:

```python
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
    
    verification = {
        "token_id": token_id,
        "token": token,
        "email": email.lower(),
        "full_name": full_name,
        "business_name": business_name,
        "metadata": metadata or {},
        "expires_at": (_now() + timedelta(hours=ttl_hours)).isoformat(),
        "created_at": _now().isoformat(),
        "used": False
    }
    
    VERIFICATION_TOKENS_COLLECTION.insert_one(verification)
    return token


def verify_and_consume_token(token: str) -> Optional[dict]:
    """Verify token and mark as used.
    
    Returns token data if valid, None if invalid/expired/used.
    """
    doc = VERIFICATION_TOKENS_COLLECTION.find_one({"token": token, "used": False})
    if not doc:
        return None
    
    expires_at = datetime.fromisoformat(doc["expires_at"])
    if _now() > expires_at:
        # Token expired
        return None
    
    # Mark as used
    VERIFICATION_TOKENS_COLLECTION.replace_one(
        {"token": token},
        {**doc, "used": True, "used_at": _now().isoformat()},
        upsert=False
    )
    
    return {
        "email": doc["email"],
        "full_name": doc["full_name"],
        "business_name": doc["business_name"],
        "metadata": doc.get("metadata", {})
    }
```

### Phase 2: Add Signup & Verify Endpoints

#### Step 2.1: Add Request/Response Models

**File**: `services/accounts/main.py` (add to existing models section)

```python
class EmailSignupRequest(BaseModel):
    """SMB-optimized signup: email + name + business info."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=120, description="Full name")
    business_name: str = Field(..., min_length=2, max_length=120, description="Business/company name")
    intent: str | None = Field(default=None, description="Signup intent: launch, ops, reporting")
    use_case: str | None = Field(default=None, description="Freeform use case description")


class EmailSignupResponse(BaseModel):
    """Response contains verification token (dev mode) or success message (production)."""
    token: str | None = Field(default=None, description="Verification token (dev mode only)")
    message: str = "Verification email sent. Check your inbox."
    email: str


class VerifyRequest(BaseModel):
    """Verify email token and complete account setup."""
    token: str


class VerifyResponse(BaseModel):
    """Complete user session info after verification."""
    jwt: str = Field(..., description="JWT authentication token")
    token: str = Field(..., description="Alias for jwt (frontend compatibility)")
    tenant_id: str
    workspace_id: str | None = Field(default=None, description="Default workspace/project ID")
    user: dict = Field(..., description="User profile data")
```

#### Step 2.2: Add Signup Endpoint

**File**: `services/accounts/main.py` (add before OAuth section)

```python
@app.post("/v1/auth/signup", response_model=EmailSignupResponse, status_code=status.HTTP_201_CREATED, tags=["auth"])
def email_signup(payload: EmailSignupRequest) -> EmailSignupResponse:
    """SMB-optimized email signup with magic link verification.
    
    Flow:
    1. Validate email not already registered
    2. Create verification token
    3. Send verification email (or return token in dev mode)
    4. User clicks link → calls /v1/auth/verify
    """
    logger.info(f"Email signup attempt: email={payload.email}, business={payload.business_name}")
    
    # Check if email already registered with any tenant
    existing_tenants = find_tenants_for_email(payload.email)
    if existing_tenants:
        logger.warning(f"Signup blocked: email {payload.email} already registered")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered. Please sign in or use a different email."
        )
    
    # Create verification token
    metadata = {
        "intent": payload.intent,
        "use_case": payload.use_case,
        "signup_method": "email",
        "signup_timestamp": datetime.utcnow().isoformat()
    }
    
    token = create_verification_token(
        email=payload.email,
        full_name=payload.name,
        business_name=payload.business_name,
        metadata=metadata,
        ttl_hours=24
    )
    
    # Production: Send verification email
    # try:
    #     verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:5179')}/verify?token={token}"
    #     await mailer.send_verification_email(
    #         to_email=payload.email,
    #         full_name=payload.name,
    #         verification_url=verification_url
    #     )
    #     logger.info(f"Verification email sent to {payload.email}")
    #     return EmailSignupResponse(email=payload.email, message="Verification email sent. Check your inbox.")
    # except Exception as e:
    #     logger.error(f"Failed to send verification email: {e}")
    #     raise HTTPException(status_code=500, detail="Failed to send verification email")
    
    # Dev mode: Return token directly for testing
    logger.info(f"Dev mode: returning verification token for {payload.email}")
    return EmailSignupResponse(
        token=token,
        email=payload.email,
        message=f"Dev mode: Use this token to verify: {token}"
    )
```

#### Step 2.3: Add Verify Endpoint

**File**: `services/accounts/main.py` (add after signup endpoint)

```python
@app.post("/v1/auth/verify", response_model=VerifyResponse, tags=["auth"])
def verify_email_token(payload: VerifyRequest) -> VerifyResponse:
    """Verify email token and complete account provisioning.
    
    Creates:
    - Tenant (organization)
    - First user account (owner)
    - Default project/workspace
    
    Returns JWT for immediate authenticated access.
    """
    logger.info(f"Email verification attempt: token={payload.token[:10]}...")
    
    # Verify and consume token
    token_data = verify_and_consume_token(payload.token)
    if not token_data:
        logger.warning(f"Verification failed: invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification token. Please request a new signup link."
        )
    
    email = token_data["email"]
    full_name = token_data["full_name"]
    business_name = token_data["business_name"]
    metadata = token_data.get("metadata", {})
    
    logger.info(f"Token verified for {email}, provisioning account...")
    
    try:
        # 1. Register tenant (organization)
        tenant = register_tenant(
            name=business_name,
            owner_email=email,
            plan_tier=PlanTier.FREE,  # Start with free trial
            metadata={
                **metadata,
                "signup_verified_at": datetime.utcnow().isoformat(),
                "verification_method": "email"
            }
        )
        logger.info(f"Created tenant {tenant.tenant_id} for {email}")
        
        # 2. Create default project/workspace
        try:
            project = create_project(
                tenant_id=tenant.tenant_id,
                name="Default Workspace",
                description="Your first workspace - customize this later"
            )
            workspace_id = project.project_id
            logger.info(f"Created default workspace {workspace_id} for tenant {tenant.tenant_id}")
        except Exception as e:
            logger.warning(f"Failed to create default workspace: {e}")
            workspace_id = None
        
        # 3. Register owner user (no password - using magic links)
        # Generate a random password since we're using passwordless auth
        random_password = secrets.token_urlsafe(32)
        user = register_user(
            tenant_id=tenant.tenant_id,
            email=email,
            full_name=full_name,
            password=random_password
        )
        logger.info(f"Created user {user.user_id} for tenant {tenant.tenant_id}")
        
        # 4. Issue JWT for authenticated session
        jwt_token = issue_jwt(user)
        
        # 5. Trigger onboarding (async task - don't block response)
        try:
            onboarding_service = TenantOnboardingService()
            # Run in background if possible, or just log
            logger.info(f"TODO: Trigger onboarding for tenant {tenant.tenant_id}")
            # asyncio.create_task(onboarding_service.run_onboarding(tenant.tenant_id))
        except Exception as e:
            logger.warning(f"Onboarding trigger failed (non-blocking): {e}")
        
        return VerifyResponse(
            jwt=jwt_token,
            token=jwt_token,  # Alias for frontend compatibility
            tenant_id=tenant.tenant_id,
            workspace_id=workspace_id,
            user={
                "id": user.user_id,
                "email": user.email,
                "name": user.full_name,
                "tenant_id": user.tenant_id
            }
        )
        
    except Exception as e:
        logger.error(f"Account provisioning failed for {email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {str(e)}"
        )
```

### Phase 3: Database Setup

#### Option A: MongoDB (Current Default)

```bash
# Connect to MongoDB
mongosh $MONGO_URI

# Create verification_tokens collection
db.createCollection("verification_tokens")

# Add index for cleanup and lookup
db.verification_tokens.createIndex({ "token": 1 }, { unique: true })
db.verification_tokens.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })
db.verification_tokens.createIndex({ "email": 1 })
db.verification_tokens.createIndex({ "used": 1 })

# Verify collections exist
db.getCollectionNames()
```

#### Option B: PostgreSQL (If using PERSISTENCE_BACKEND=postgres)

```sql
-- Create verification_tokens table
CREATE TABLE verification_tokens (
    token_id VARCHAR(255) PRIMARY KEY,
    token VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}',
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP
);

-- Add indexes
CREATE INDEX idx_verification_tokens_token ON verification_tokens(token);
CREATE INDEX idx_verification_tokens_email ON verification_tokens(email);
CREATE INDEX idx_verification_tokens_expires ON verification_tokens(expires_at);
CREATE INDEX idx_verification_tokens_used ON verification_tokens(used);

-- Verify
\dt verification_tokens
```

### Phase 4: Environment Configuration

**File**: `.env` or `.env.smb`

```bash
# Persistence
PERSISTENCE_BACKEND=mongodb  # or postgres
MONGO_URI=mongodb://localhost:27017/dyocense
# or
POSTGRES_URL=postgresql://user:pass@localhost:5432/dyocense

# Auth
ACCOUNTS_JWT_SECRET=your-secret-key-here  # Generate: openssl rand -hex 32
ACCOUNTS_JWT_TTL=1440  # 24 hours in minutes

# Email (for production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@dyocense.com
SMTP_PASSWORD=app-specific-password
FRONTEND_URL=http://localhost:5179  # For verification links

# Dev mode (returns token instead of sending email)
ENVIRONMENT=development  # or production
```

### Phase 5: Testing

#### Test 1: Signup

```bash
curl -X POST http://localhost:8001/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "business_name": "Test Shop",
    "intent": "launch",
    "use_case": "Testing the signup flow"
  }'

# Expected response (dev mode):
{
  "token": "abc123...",
  "email": "test@example.com",
  "message": "Dev mode: Use this token to verify: abc123..."
}
```

#### Test 2: Verify

```bash
curl -X POST http://localhost:8001/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123..."
  }'

# Expected response:
{
  "jwt": "eyJ...",
  "token": "eyJ...",
  "tenant_id": "test-shop-a1b2c3",
  "workspace_id": "project-xyz...",
  "user": {
    "id": "user-abc123...",
    "email": "test@example.com",
    "name": "Test User",
    "tenant_id": "test-shop-a1b2c3"
  }
}
```

#### Test 3: Use JWT

```bash
curl http://localhost:8001/v1/tenants/me/profile \
  -H "Authorization: Bearer eyJ..."

# Should return tenant profile
```

#### Test 4: Frontend E2E

```bash
# 1. Start backend
uvicorn services.kernel.main:app --reload --port 8001

# 2. Start frontend
cd apps/smb && npm run dev

# 3. Visit http://localhost:5179/signup
# 4. Fill form and submit
# 5. Should redirect to /verify?token=xxx&next=/home
# 6. Should auto-verify and show dashboard
```

## Summary of Changes

### Files to Modify

1. **`packages/accounts/models.py`**
   - Add `VerificationToken` model

2. **`packages/accounts/repository.py`**
   - Add `VERIFICATION_TOKENS_COLLECTION`
   - Add `create_verification_token()`
   - Add `verify_and_consume_token()`

3. **`services/accounts/main.py`**
   - Add `EmailSignupRequest`, `EmailSignupResponse`
   - Add `VerifyRequest`, `VerifyResponse`
   - Add `POST /v1/auth/signup` endpoint
   - Add `POST /v1/auth/verify` endpoint

4. **Database**
   - Create `verification_tokens` collection/table
   - Add indexes

5. **`.env`**
   - Add `ACCOUNTS_JWT_SECRET`
   - Add email settings (optional for dev)

### No Frontend Changes Needed ✅

The frontend is already correctly calling:

- `POST /v1/auth/signup` with the right payload
- `POST /v1/auth/verify` with the right token format

## Implementation Checklist

- [ ] Phase 1: Add verification token model and repository functions
- [ ] Phase 2: Add signup and verify endpoints to accounts service
- [ ] Phase 3: Set up database collection/table with indexes
- [ ] Phase 4: Configure environment variables
- [ ] Phase 5: Test signup → verify → login flow
- [ ] Phase 6: (Optional) Add email sending for production
- [ ] Phase 7: Update CORS settings if needed
- [ ] Phase 8: Add monitoring/logging for signup events

## Next Steps

1. **Immediate**: Implement Phase 1 & 2 (models + endpoints)
2. **Database**: Run MongoDB or PostgreSQL setup commands
3. **Test**: Use cURL to verify endpoints work
4. **Frontend**: Test complete flow in browser
5. **Production**: Add email service integration
6. **Polish**: Add rate limiting, better error messages, analytics

## Success Criteria

- ✅ User can signup with email from frontend
- ✅ Verification token created and returned (dev mode)
- ✅ User can verify token and get JWT
- ✅ Tenant, user, and workspace created automatically
- ✅ User redirected to authenticated dashboard
- ✅ JWT works for subsequent API calls
- ✅ Data persists across server restarts
- ✅ No more dev token fallbacks
