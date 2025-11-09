# Get Started Flow - End-to-End Review

**Date**: November 9, 2025  
**Status**: ⚠️ PARTIALLY INTEGRATED - Missing Backend Services

## Executive Summary

The SMB frontend signup flow is well-implemented but **NOT fully integrated with running backend services**. Critical auth endpoints (`/v1/auth/signup`, `/v1/auth/verify`) exist in **multiple services** but none are currently active in the main kernel.

## Current Architecture

### Frontend Flow (✅ Complete)

```
Landing Page → Signup Form → Verify Page → Home Dashboard
     ↓              ↓              ↓              ↓
  /signup       /v1/auth/      /v1/auth/    /v1/tenants/
                 signup         verify      {tenant}/plans
```

### Backend Services (⚠️ Fragmented)

**Three different auth implementations found:**

1. **`services/agent_shell/main.py`** (Standalone, NOT mounted)
   - `/v1/auth/signup` → Creates user, tenant, workspace, returns verification token
   - `/v1/auth/verify` → Validates token, returns JWT
   - Status: ❌ Not integrated into kernel

2. **`services/keystone_proxy/main.py`** (Standalone, NOT mounted)
   - `/v1/auth/verify` only (no signup endpoint)
   - Status: ❌ Not integrated into kernel

3. **`services/accounts/main.py`** (OAuth-focused, MOUNTED in kernel)
   - `/v1/auth/providers` → List OAuth providers
   - `/v1/auth/{provider}/authorize` → OAuth redirect
   - `/v1/auth/{provider}/callback` → OAuth callback
   - Status: ✅ Mounted but **missing email/password signup**

## Critical Gaps

### 🔴 Gap 1: No Active Signup Endpoint

**Problem**: Frontend calls `/v1/auth/signup`, but:

- `agent_shell` has it but isn't mounted in kernel
- `accounts` service doesn't have it (OAuth only)
- Result: **Signup always fails**, falls back to dev token

**Evidence**:

```typescript
// apps/smb/src/pages/Signup.tsx:43
const response = await tryPost<{ token?: string }>('/v1/auth/signup', {
    email: values.email,
    name: values.fullName,
    business_name: values.businessName,
    intent: toolHint ?? values.goal,
    use_case: values.useCase,
})
```

```python
# services/kernel/main.py - SUB_APPS list
SUB_APPS = [
    accounts_app,        # ✅ Has OAuth, ❌ No email signup
    chat_app,
    compiler_app,
    # ... agent_shell is NOT in this list
]
```

### 🔴 Gap 2: Verify Endpoint Mismatch

**Problem**: Frontend expects specific response shape:

```typescript
{ jwt?: string; token?: string; tenant_id?: string; user?: any }
```

**Current implementations vary**:

- `agent_shell`: Returns `{ user_id, tenant_id, workspace_id, jwt }`
- `keystone_proxy`: Returns dynamic structure
- Neither is mounted in kernel at `/v1/auth/verify`

### 🔴 Gap 3: Missing Tenant/Workspace Creation

**Problem**: After signup, user needs:

1. User account
2. Tenant (organization)
3. Default workspace
4. Access token (JWT)

**Current state**:

- `agent_shell` does this correctly but isn't active
- `accounts` service has no tenant/workspace logic
- Frontend falls back to localStorage dev tokens

## User Journey (Current Behavior)

### 1. Landing Page (`/`)

- ✅ Works: Shows hero, features, templates
- ✅ Works: "Get Started" → `/signup`

### 2. Signup (`/signup`)

```typescript
// What happens:
1. User fills form (name, email, business, goal)
2. Frontend POSTs to /v1/auth/signup
3. ❌ Request fails (endpoint not mounted)
4. ⚠️ Fallback: Creates dev-token-{timestamp}
5. Navigate to /verify?token=dev-token-xxx&next=/home
```

**API Call**:

```bash
POST http://localhost:8001/v1/auth/signup
{
  "email": "owner@example.com",
  "name": "Alex Kim",
  "business_name": "Northwind Cafe",
  "intent": "launch",
  "use_case": "Need help syncing Shopify promos"
}

# Expected: { token: "verify-token-xxx" }
# Actual: ❌ 404 Not Found → fallback to dev token
```

### 3. Verify (`/verify`)

```typescript
// What happens:
1. Extracts token from URL params
2. POSTs to /v1/auth/verify with { token }
3. ❌ Request fails (endpoint not mounted)
4. ⚠️ Fallback: Creates dev-jwt and dev-tenant
5. Stores in localStorage: { apiToken, tenantId }
6. Navigate to /home
```

**API Call**:

```bash
POST http://localhost:8001/v1/auth/verify
{ "token": "dev-token-1731205620" }

# Expected: { jwt, tenant_id, workspace_id, user }
# Actual: ❌ 404 Not Found → fallback to dev credentials
```

### 4. Home Dashboard (`/home`)

```typescript
// What happens:
1. RequireAuth checks localStorage for apiToken
2. ✅ Token exists (dev-jwt)
3. Fetches /v1/tenants/{tenantId}/plans
4. ⚠️ May fail if tenantId invalid
5. Shows onboarding modal if no plans
```

**API Call**:

```bash
GET http://localhost:8001/v1/tenants/dev-tenant/plans
Authorization: Bearer dev-jwt

# Status: Depends on smb_gateway being mounted
```

## Working vs Broken

### ✅ What Works

1. **UI Flow**: All pages render correctly
2. **Form Validation**: React Hook Form + Mantine inputs
3. **Auth State Management**: Zustand store with localStorage persistence
4. **Routing**: Public/Platform layout separation
5. **Error Handling**: Graceful fallback to dev tokens
6. **Visual Design**: Professional UX with proper contrast

### ❌ What's Broken

1. **Signup**: Always fails, uses dev token
2. **Email Verification**: Never validates real tokens
3. **Tenant Creation**: Never creates real tenants
4. **User Profiles**: No real user data stored
5. **Session Management**: Relies on localStorage only
6. **OAuth Integration**: Exists but not wired to frontend

## Backend Integration Requirements

### Immediate Fixes Needed

#### Option A: Mount Agent Shell (Quick Fix)

```python
# services/kernel/main.py
from services.agent_shell.main import app as agent_shell_app

SUB_APPS = [
    accounts_app,
    agent_shell_app,  # ← ADD THIS
    chat_app,
    # ...
]
```

**Pros**: Fastest path to working auth
**Cons**: agent_shell uses in-memory dicts (not persistent)

#### Option B: Extend Accounts Service (Production Fix)

Add to `services/accounts/main.py`:

```python
@app.post("/v1/auth/signup")
async def email_signup(
    email: str,
    name: str,
    business_name: str,
    intent: str = None,
    use_case: str = None
):
    # 1. Create user in database
    user = await create_user(email=email, name=name)
    
    # 2. Create tenant
    tenant = await create_tenant(
        name=business_name,
        owner_id=user.id
    )
    
    # 3. Create default workspace
    workspace = await create_workspace(
        tenant_id=tenant.id,
        name="Default Workspace"
    )
    
    # 4. Generate verification token
    token = generate_verification_token(user.id)
    
    # 5. Send email (or return token for dev)
    await send_verification_email(email, token)
    
    return {"token": token}  # Dev mode: return token
```

```python
@app.post("/v1/auth/verify")
async def verify_email(token: str):
    # 1. Validate token
    user_id = validate_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid token")
    
    # 2. Activate user
    user = await activate_user(user_id)
    
    # 3. Get tenant/workspace
    tenant = await get_user_tenant(user_id)
    workspace = await get_default_workspace(tenant.id)
    
    # 4. Generate JWT
    jwt = generate_jwt(user_id, tenant.id)
    
    return {
        "jwt": jwt,
        "token": jwt,  # Alias for compatibility
        "tenant_id": tenant.id,
        "workspace_id": workspace.id,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }
```

### Database Schema Needed

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    owner_user_id UUID REFERENCES users(id),
    plan VARCHAR DEFAULT 'trial',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workspaces table
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Verification tokens table
CREATE TABLE verification_tokens (
    token VARCHAR PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Environment Configuration

### Current Config (`apps/smb/src/lib/api.ts`)

```typescript
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'
```

### Required `.env` (apps/smb/)

```bash
VITE_API_BASE=http://localhost:8001
# VITE_PROXY_API_KEY=optional-for-hardened-proxy
```

### Backend `.env` Required

```bash
# Database
MONGO_URI=mongodb://localhost:27017/dyocense
# or
POSTGRES_URL=postgresql://user:pass@localhost:5432/dyocense

# Auth
ACCOUNTS_JWT_SECRET=your-secret-key-here
ACCOUNTS_JWT_TTL=1440  # 24 hours

# Email (for verification links)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@dyocense.com
SMTP_PASS=app-specific-password
```

## Testing the Flow

### Manual Test (After Fixes)

```bash
# 1. Start backend
cd /Users/balu/Projects/dyocense
source .venv/bin/activate
uvicorn services.kernel.main:app --reload --host 127.0.0.1 --port 8001

# 2. Start frontend
cd apps/smb
npm run dev

# 3. Test signup
# Visit http://localhost:5179/signup
# Fill form:
#   Name: Test User
#   Business: Test Shop
#   Email: test@example.com
# Submit

# 4. Check logs for:
# - POST /v1/auth/signup (should return token)
# - User/tenant/workspace created
# - Redirect to /verify?token=xxx

# 5. Verify should:
# - Validate token
# - Return JWT
# - Redirect to /home
# - Show dashboard with workspace
```

### API Test (cURL)

```bash
# Test signup
curl -X POST http://localhost:8001/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "business_name": "Test Shop",
    "intent": "launch",
    "use_case": "Testing signup flow"
  }'

# Expected: {"token": "verify-abc123..."}

# Test verify
curl -X POST http://localhost:8001/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "verify-abc123..."}'

# Expected: {"jwt": "...", "tenant_id": "...", "workspace_id": "...", "user": {...}}
```

## Recommendations

### Priority 1 (Critical - Blocking Users)

1. ✅ **Choose auth strategy**: Option A (quick) or Option B (production)
2. ✅ **Mount auth endpoints** in kernel
3. ✅ **Test signup → verify → home flow**
4. ✅ **Add database persistence** (replace in-memory dicts)

### Priority 2 (Important - UX)

1. ⚠️ **Email verification**: Send actual emails instead of returning tokens
2. ⚠️ **Better error messages**: Show user-friendly errors on signup failure
3. ⚠️ **Loading states**: Add skeleton loaders during auth
4. ⚠️ **Resend verification**: Allow users to request new link

### Priority 3 (Enhancement - Polish)

1. 📋 **Password auth**: Add optional password alongside magic links
2. 📋 **Social login**: Wire up existing OAuth to frontend
3. 📋 **Multi-workspace**: Let users create/switch workspaces
4. 📋 **Team invites**: Allow workspace sharing

## Files to Update

### Backend (Choose Option A or B)

**Option A Files**:

- `services/kernel/main.py` - Add agent_shell to SUB_APPS
- `services/agent_shell/main.py` - Add database persistence

**Option B Files**:

- `services/accounts/main.py` - Add signup/verify endpoints
- `packages/kernel_common/persistence.py` - Add user/tenant models
- `services/accounts/models.py` - Add User, Tenant, Workspace models

### Frontend (No changes needed if backend matches contract)

- ✅ `apps/smb/src/pages/Signup.tsx` - Already correct
- ✅ `apps/smb/src/pages/Verify.tsx` - Already correct
- ✅ `apps/smb/src/stores/auth.ts` - Already correct
- ✅ `apps/smb/src/lib/api.ts` - Already correct

## Success Criteria

Flow is "fully integrated" when:

- [ ] User can fill signup form
- [ ] POST `/v1/auth/signup` returns real verification token
- [ ] User/tenant/workspace created in database
- [ ] POST `/v1/auth/verify` validates token and returns JWT
- [ ] JWT works for authenticated API calls
- [ ] `/home` loads user's actual tenant data
- [ ] No dev token fallbacks triggered
- [ ] Flow works after server restart (persistence)

## Current Status: NOT INTEGRATED ❌

**Reason**: Auth endpoints exist but aren't mounted in running kernel service. Frontend works correctly but always falls back to dev mode because backend returns 404 for `/v1/auth/*`.

**Next Step**: Choose Option A (quick fix) or Option B (production fix) and implement.
