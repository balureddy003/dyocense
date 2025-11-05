# Phase 1 Deployment Guide

## ✅ What's Been Implemented

1. **Keycloak Integration** - Full Admin API wrapper for realm and user management
2. **Tenant Onboarding Service** - Orchestrates Keycloak provisioning  
3. **Backend APIs**:
   - `POST /v1/tenants/register` - Creates tenant with Keycloak realm
   - `GET /v1/tenants/me/onboarding` - Returns login credentials
   - `POST /v1/tenants/me/cancel` - Cancels subscription and cleans up
4. **Simplified UI** - 3-step purchase flow for SMBs
5. **Graceful Fallbacks** - Works with or without Keycloak

## 🚀 Getting Started

### Prerequisites

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Should include python-keycloak>=3.0,<4
pip list | grep keycloak
```

### Option 1: Development (Without Keycloak)

If you don't want to set up Keycloak yet, just start the services:

```bash
# Terminal 1: Backend
python -m uvicorn services.accounts.main:app --reload --port 8000

# Terminal 2: UI
cd apps/ui && npm run dev
```

The system will:
- ✅ Create tenants in MongoDB
- ✅ Generate demo API tokens
- ⚠️ Skip Keycloak realm creation (graceful fallback)

### Option 2: Development (With Keycloak)

#### Step 1: Update `.env` File

Add Keycloak configuration:

```properties
# For development, use username/password:
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_CLIENT_ID=admin-cli
KEYCLOAK_USERNAME=admin
KEYCLOAK_PASSWORD=admin
```

#### Step 2: Start Keycloak

```bash
docker compose up -d keycloak
```

Wait ~30 seconds for it to start. Verify:

```bash
curl http://localhost:8080/auth/realms/master
# Should return JSON, not 404
```

#### Step 3: Start Backend

```bash
python -m uvicorn services.accounts.main:app --reload --port 8000
```

Should see:
```
✅ Connected to Keycloak at http://localhost:8080
```

If you see a warning instead, check `.env` configuration.

#### Step 4: Start UI

```bash
cd apps/ui && npm run dev
```

#### Step 5: Test the Flow

1. Open http://localhost:5173/buy
2. Select plan
3. Enter org name + email
4. Click "Create Account"
5. Check Keycloak: http://localhost:8080/auth/admin
   - New realm should be created
   - User should be visible

## 📋 Configuration Files

### Updated Files

| File | Changes |
|------|---------|
| `.env` | Added Keycloak env vars (optional) |
| `services/accounts/main.py` | Keycloak initialization with fallback |
| `packages/trust/onboarding.py` | Accept Keycloak credentials as params |
| `packages/trust/__init__.py` | Export Keycloak modules |
| `requirements-dev.txt` | Added python-keycloak |

### New Files

| File | Purpose |
|------|---------|
| `KEYCLOAK_CONFIG.md` | Detailed Keycloak setup guide |
| `PHASE1_IMPLEMENTATION.md` | Implementation summary |
| `packages/trust/keycloak_admin.py` | Keycloak Admin API wrapper |
| `packages/trust/onboarding.py` | Tenant onboarding service |

## 🔧 Troubleshooting

### "Failed to initialize Keycloak client"

This is expected if Keycloak isn't configured. The system will:
- Log a warning
- Continue without Keycloak
- Use demo tokens instead

### "Cannot find name 'OnboardingDetails'"

The TypeScript interface was added to `apps/ui/src/lib/api.ts`. Make sure you have:

```typescript
export interface OnboardingDetails {
  tenant_id: string;
  keycloak_realm: string | null;
  keycloak_url: string | null;
  temporary_password: string | null;
  username: string | null;
  email: string;
  login_url: string | null;
  status: "ready" | "pending_keycloak_setup";
  message?: string;
}
```

### Backend won't start with "Status code 204 must not have a response body"

Already fixed! The DELETE endpoint at `/v1/users/api-tokens/{token_id}` had a return type annotation that conflicted with the 204 status code.

## ✨ Key Design Decisions

1. **Non-blocking Keycloak** - System works with or without it
2. **Optional credentials** - Keycloak only initializes if creds provided
3. **Temporary passwords** - Forced reset on first login for security
4. **Per-tenant realms** - Complete data isolation
5. **Fallback tokens** - Demo tokens when Keycloak unavailable

## 📊 Success Criteria

- [x] Keycloak integration implemented
- [x] Tenant registration creates realms
- [x] Users provisioned with temp passwords
- [x] Simple SMB-focused UI
- [x] Graceful fallback when Keycloak unavailable
- [x] Type-safe frontend code
- [x] All tests passing (no 204 response body errors)

## 🎯 What Happens During Signup

```
User fills out form
  ↓
POST /v1/tenants/register
  ├─ Create tenant in MongoDB
  ├─ IF Keycloak configured:
  │   ├─ Create Keycloak realm
  │   ├─ Create user in realm
  │   └─ Generate temporary password
  └─ ELSE: Generate demo token
  ↓
GET /v1/tenants/me/onboarding
  ├─ Return credentials
  └─ Show next steps
  ↓
User redirected to login
```

## 📚 Next Steps (Phase 2)

1. **Email Notifications** - Send onboarding link + credentials
2. **Team Management** - Invite members during signup
3. **Trial Expiration** - Auto-downgrade after trial period
4. **Usage Tracking** - Monitor SMB usage patterns
5. **Admin Dashboard** - Manage tenants and subscriptions
6. **Webhook Integration** - Listen to Keycloak events

## 🐛 Known Issues & Limitations

1. **Keycloak not auto-starting** - Must run `docker compose up -d keycloak` manually
2. **Demo tokens not in header** - UI shows credentials but doesn't auto-add auth header
3. **No email sending** - Credentials not emailed to user yet (Phase 2)
4. **Single user per realm** - Only owner provisioned, team members added later (Phase 2)

## 📞 Support

For Keycloak configuration issues, see: `KEYCLOAK_CONFIG.md`

For implementation details, see: `PHASE1_IMPLEMENTATION.md`

For API documentation, check the FastAPI docs at: `http://localhost:8000/docs`
