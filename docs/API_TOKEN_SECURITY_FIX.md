# API Token Security Fix - Phase 2 Enhancement

## Problem Identified

**Security Issue**: API tokens were being sent via email during tenant registration, which is:
- ❌ Insecure (emails can be intercepted/forwarded)
- ❌ Wrong UX (users shouldn't handle API tokens for registration)
- ❌ Confusing flow (mixing programmatic access with user authentication)

## Solution Implemented

### 1. Backend Changes

#### Removed API Token from Welcome Email
**File**: `services/accounts/main.py`

**Before**:
```python
text = (
    f"Tenant ID: {tenant.tenant_id}\n"
    f"API Token: {tenant.api_token}\n"  # ❌ Security risk
    f"Temporary Password: {temp_pass}\n"
)
```

**After**:
```python
text = (
    f"Tenant ID: {tenant.tenant_id}\n"
    f"Temporary Password: {temp_pass}\n"  # ✅ Only temporary password
    f"\nYou'll be prompted to create a permanent password on first login.\n"
)
```

#### Changed User Registration Flow
**Before**: Required `access_token` (tenant API token)
**After**: Requires `temporary_password` (from welcome email)

```python
class UserRegistrationRequest(BaseModel):
    tenant_id: str
    email: EmailStr
    full_name: str
    password: str
    temporary_password: str  # ✅ Changed from access_token
```

Registration endpoint now:
1. Verifies temporary password from tenant metadata
2. Creates user account
3. Clears temporary password after successful registration

#### Added API Token Management Endpoints

**GET /v1/tenants/me/api-token**
- View tenant API token (authenticated users only)
- Returns token with security note

**POST /v1/tenants/me/api-token/rotate**
- Rotate (regenerate) API token
- Invalidates old token immediately
- Requires user authentication (not API token)

### 2. Frontend Changes

#### Updated Registration Form
**File**: `apps/ui/src/pages/LoginPage.tsx`

- Label changed: "Access token" → "Temporary Password"
- Placeholder updated for clarity
- Help text: "Need an account? Register with your temporary password"

#### Created Settings Page
**New File**: `apps/ui/src/pages/SettingsPage.tsx`

Features:
- View profile (business name, tenant ID, email)
- **API Token Management**:
  - Show/hide API token
  - Copy to clipboard
  - Rotate token
  - Usage instructions with curl example
  - Security warning

#### Added Navigation
- Settings icon added to TopNav (gear icon)
- Route: `/settings` (requires authentication)

### 3. Type System Updates

**TypeScript Interfaces**:
```typescript
// api.ts
interface UserRegistrationPayload {
  temporary_password: string;  // ✅ Changed from access_token
}

// AuthContext.tsx
interface AuthUser {
  tenantId?: string;  // ✅ Added for Settings page
}

registerUserAccount: (
  tenantId: string,
  email: string,
  fullName: string,
  password: string,
  temporaryPassword: string  // ✅ Changed parameter name
) => Promise<void>;
```

## New User Flow

### Tenant Registration
1. User registers organization via UI
2. **Welcome email sent** with:
   - Tenant ID
   - Temporary password (single-use)
   - Login link
3. User clicks login link → pre-fills tenant ID and email

### First-Time User Registration
1. On login page, click "Need an account? Register with your temporary password"
2. Enter:
   - Temporary password (from email)
   - Full name
   - New permanent password
3. Registration creates user account and clears temporary password
4. User can now login with email + permanent password

### API Token Access (Post-Login)
1. User logs in successfully
2. Navigates to Settings (gear icon in nav)
3. Clicks "Show API Token"
4. Can:
   - Copy token
   - Rotate token (invalidates old one)
   - View usage instructions

## Security Improvements

✅ **No sensitive tokens in email** - Only temporary single-use passwords
✅ **Temporary passwords auto-cleared** - After successful registration
✅ **API tokens behind auth** - Must login to view/manage
✅ **Token rotation** - Users can invalidate compromised tokens
✅ **User-initiated access** - API tokens only visible when explicitly requested
✅ **Security warnings** - Clear messaging about token sensitivity

## Migration Notes

### Breaking Changes
⚠️ **Frontend**: `registerUserAccount()` parameter changed from `accessToken` to `temporaryPassword`
⚠️ **Backend**: `/v1/users/register` payload changed from `access_token` to `temporary_password`

### Backward Compatibility
- Existing tenants with API tokens are unaffected
- API token authentication still works for programmatic access
- No database migration required (temporary_password already in metadata)

## Testing Checklist

- [ ] Register new tenant → receive email with temporary password (no API token)
- [ ] Click login link → switch to registration mode
- [ ] Register with temporary password → creates user account
- [ ] Login with new credentials → successful
- [ ] Navigate to Settings → view profile
- [ ] Show API token → displays tenant API token
- [ ] Copy token → clipboard works
- [ ] Rotate token → generates new token, old one invalidated
- [ ] Use rotated token in API call → works
- [ ] Try old token → should fail (401)

## API Documentation Updates

### New Endpoints

```
GET /v1/tenants/me/api-token
Authentication: Bearer token (user JWT)
Response: { tenant_id, api_token, note }

POST /v1/tenants/me/api-token/rotate  
Authentication: Bearer token (user JWT)
Response: { tenant_id, api_token, note }
```

### Modified Endpoints

```
POST /v1/users/register
Body: {
  tenant_id: string
  email: string
  full_name: string
  password: string
  temporary_password: string  // ⚠️ Changed from access_token
}
```

## Files Modified

### Backend
- `services/accounts/main.py` (3 sections)
  - UserRegistrationRequest model
  - register_new_user endpoint
  - Onboarding email template
  - Added API token endpoints

### Frontend
- `apps/ui/src/lib/api.ts` - Updated UserRegistrationPayload
- `apps/ui/src/context/AuthContext.tsx` - Updated AuthUser and registerUserAccount
- `apps/ui/src/pages/LoginPage.tsx` - Updated registration form UI
- `apps/ui/src/pages/SettingsPage.tsx` - **NEW** API token management
- `apps/ui/src/pages/App.tsx` - Added /settings route
- `apps/ui/src/components/TopNav.tsx` - Added Settings link

## Next Steps

1. **Test the complete flow** end-to-end
2. **Update API documentation** (OpenAPI spec)
3. **Consider adding**:
   - API token expiration dates
   - Multiple API tokens per tenant
   - Token scopes/permissions
   - Audit log for token usage
4. **Email template improvements**:
   - HTML formatting
   - Better branding
   - Password complexity requirements
