# Get Started Flow - Backend Integration Action Plan

## Current Status: ❌ NOT INTEGRATED

**Finding**: The signup flow endpoints (`/v1/auth/signup` and `/v1/auth/verify`) **do not exist** in the running backend.

**Evidence**:

```bash
# Test signup endpoint
$ curl http://localhost:8001/v1/auth/signup
{"detail":"Not Found"}

# Check available auth endpoints
$ curl http://localhost:8001/openapi.json | grep auth paths
/v1/auth/providers            # ✅ OAuth providers (empty)
/v1/auth/{provider}/authorize # ✅ OAuth redirect
/v1/auth/{provider}/callback  # ✅ OAuth callback
# ❌ Missing: /v1/auth/signup
# ❌ Missing: /v1/auth/verify
```

## Problem Summary

1. **Frontend expects**: `/v1/auth/signup` and `/v1/auth/verify`
2. **Backend has**: Only OAuth endpoints (Google, Microsoft, etc.)
3. **Result**: All signups fail → fallback to dev tokens
4. **Impact**: Users can't create real accounts

## Solution: Add Email/Password Signup to Accounts Service

### Step 1: Add Signup Endpoint

Add to `services/accounts/main.py`:

```python
from pydantic import EmailStr

class EmailSignupRequest(BaseModel):
    email: EmailStr
    name: str
    business_name: str = None
    intent: str = None
    use_case: str = None

class EmailSignupResponse(BaseModel):
    token: str  # Verification token for dev, or success message for prod

@app.post("/v1/auth/signup", response_model=EmailSignupResponse, tags=["auth"])
async def email_signup(req: EmailSignupRequest):
    """
    Email-based signup for SMB users.
    Creates user, tenant, workspace, and sends verification email.
    """
    # 1. Check if user exists
    existing = await db.users.find_one({"email": req.email})
    if existing:
        raise HTTPException(409, "Email already registered")
    
    # 2. Create user
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": req.email,
        "name": req.name,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "metadata": {
            "intent": req.intent,
            "use_case": req.use_case
        }
    }
    await db.users.insert_one(user)
    
    # 3. Create tenant
    tenant_id = str(uuid.uuid4())
    tenant = {
        "id": tenant_id,
        "name": req.business_name or f"{req.name}'s Business",
        "owner_user_id": user_id,
        "plan": "trial",
        "created_at": datetime.utcnow().isoformat()
    }
    await db.tenants.insert_one(tenant)
    
    # 4. Create default workspace
    workspace_id = str(uuid.uuid4())
    workspace = {
        "id": workspace_id,
        "tenant_id": tenant_id,
        "name": "Default Workspace",
        "created_at": datetime.utcnow().isoformat()
    }
    await db.workspaces.insert_one(workspace)
    
    # 5. Generate verification token
    token = secrets.token_urlsafe(32)
    await db.verification_tokens.insert_one({
        "token": token,
        "user_id": user_id,
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "created_at": datetime.utcnow().isoformat()
    })
    
    # 6. TODO: Send verification email in production
    # await send_verification_email(req.email, token)
    
    # 7. For dev: return token directly
    return EmailSignupResponse(token=token)
```

### Step 2: Add Verify Endpoint

```python
class VerifyRequest(BaseModel):
    token: str

class VerifyResponse(BaseModel):
    jwt: str
    token: str  # Alias for jwt (frontend compatibility)
    tenant_id: str
    workspace_id: str = None
    user: dict

@app.post("/v1/auth/verify", response_model=VerifyResponse, tags=["auth"])
async def verify_email(req: VerifyRequest):
    """
    Verify email token and return JWT for authenticated access.
    """
    # 1. Find and validate token
    token_doc = await db.verification_tokens.find_one({"token": req.token})
    if not token_doc:
        raise HTTPException(401, "Invalid verification token")
    
    # 2. Check expiration
    expires_at = datetime.fromisoformat(token_doc["expires_at"])
    if datetime.utcnow() > expires_at:
        await db.verification_tokens.delete_one({"token": req.token})
        raise HTTPException(401, "Verification token expired")
    
    # 3. Get user and activate
    user_id = token_doc["user_id"]
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(404, "User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"status": "active"}}
    )
    
    # 4. Get tenant and workspace
    tenant = await db.tenants.find_one({"owner_user_id": user_id})
    workspace = await db.workspaces.find_one({"tenant_id": tenant["id"]})
    
    # 5. Generate JWT
    jwt_payload = {
        "user_id": user_id,
        "tenant_id": tenant["id"],
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    jwt_token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")
    
    # 6. Delete used token
    await db.verification_tokens.delete_one({"token": req.token})
    
    return VerifyResponse(
        jwt=jwt_token,
        token=jwt_token,  # Alias
        tenant_id=tenant["id"],
        workspace_id=workspace["id"] if workspace else None,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    )
```

### Step 3: Add Required Imports

At top of `services/accounts/main.py`:

```python
import secrets
import jwt
from datetime import datetime, timedelta
```

### Step 4: Environment Variables

Add to `.env`:

```bash
# JWT Secret (generate with: openssl rand -hex 32)
ACCOUNTS_JWT_SECRET=your-secret-key-here
ACCOUNTS_JWT_TTL=10080  # 7 days in minutes
```

### Step 5: Database Collections

Ensure MongoDB has these collections:

```javascript
// Run in MongoDB shell
db.createCollection("users");
db.createCollection("tenants");
db.createCollection("workspaces");
db.createCollection("verification_tokens");

// Add indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.verification_tokens.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
```

## Testing After Implementation

### 1. Test Signup

```bash
curl -X POST http://localhost:8001/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "business_name": "Test Shop",
    "intent": "launch",
    "use_case": "Testing signup"
  }'

# Expected: {"token": "Ab3Cd..."}
```

### 2. Test Verify

```bash
curl -X POST http://localhost:8001/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "Ab3Cd..."}'

# Expected: 
# {
#   "jwt": "eyJ...",
#   "token": "eyJ...",
#   "tenant_id": "uuid...",
#   "workspace_id": "uuid...",
#   "user": {"id": "...", "email": "...", "name": "..."}
# }
```

### 3. Test Frontend Flow

1. Visit `http://localhost:5179/signup`
2. Fill form with test data
3. Submit
4. Should redirect to `/verify?token=xxx&next=/home`
5. Should auto-verify and redirect to `/home`
6. Should show dashboard with workspace name

## Alternative: Quick Fix with Agent Shell

If you need immediate testing without modifying accounts service:

### Option A: Mount Existing Agent Shell

```python
# services/kernel/main.py
from services.agent_shell.main import app as agent_shell_app

SUB_APPS = [
    accounts_app,
    agent_shell_app,  # ← ADD THIS LINE
    chat_app,
    # ...
]
```

**Pros**:

- Works immediately
- No code changes needed

**Cons**:

- Uses in-memory storage (data lost on restart)
- Not production-ready
- Separate from accounts service

### Option B: Standalone Service

Run agent_shell separately:

```bash
# Terminal 1: Main kernel (port 8001)
uvicorn services.kernel.main:app --reload --port 8001

# Terminal 2: Agent shell (port 8002)
uvicorn services.agent_shell.main:app --reload --port 8002
```

Update frontend:

```typescript
// apps/smb/src/lib/api.ts
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8002'
```

## Recommendation

**Use the full solution** (Add to accounts service) because:

1. ✅ Production-ready with database persistence
2. ✅ All auth in one service (OAuth + email)
3. ✅ Proper token expiration and security
4. ✅ Works with existing accounts infrastructure
5. ✅ Frontend needs no changes

## Files to Modify

1. `services/accounts/main.py` - Add signup/verify endpoints
2. `.env` - Add JWT_SECRET
3. Database - Add collections/indexes

## Success Criteria

- [ ] POST `/v1/auth/signup` returns verification token
- [ ] POST `/v1/auth/verify` returns JWT and tenant info
- [ ] User/tenant/workspace persisted in database
- [ ] Frontend signup flow works end-to-end
- [ ] Data survives server restart
- [ ] No dev token fallbacks triggered

## Current Blockers

1. ❌ `/v1/auth/signup` endpoint doesn't exist
2. ❌ `/v1/auth/verify` endpoint doesn't exist
3. ❌ No email-based auth in accounts service
4. ❌ Frontend always fails → dev mode

**Once implemented**: All 4 blockers resolved, signup flow fully functional.
