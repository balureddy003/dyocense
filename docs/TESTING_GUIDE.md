# End-to-End Testing Guide - Phase 2 Features

This guide walks you through testing all Phase 2 features including invitations, admin dashboard, and trial enforcement.

## Prerequisites

✅ Docker Compose services running (MongoDB, Keycloak)
✅ Backend service running on port 8001
✅ Frontend UI running on port 5173

## Test Flow

### 1. Health Check & Background Jobs

**Verify service is healthy:**
```bash
curl http://127.0.0.1:8001/health | jq
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "accounts",
  "background_jobs": {
    "trial_enforcement": {
      "running": true,
      "enabled": true,
      "interval": "24 hours"
    }
  }
}
```

### 2. Register New Tenant (Silver Trial)

**Register a test organization:**
```bash
curl -X POST http://127.0.0.1:8001/v1/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "owner_email": "owner@test.com",
    "plan_tier": "silver",
    "metadata": {}
  }' | jq
```

**Save the response:**
- Copy the `tenant_id`
- Copy the `api_token`

### 3. Test Tenant Profile

**Get tenant details:**
```bash
curl http://127.0.0.1:8001/v1/tenants/me \
  -H "Authorization: Bearer YOUR_API_TOKEN" | jq
```

### 4. Invite Teammates

**Create an invitation:**
```bash
curl -X POST http://127.0.0.1:8001/v1/invitations \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invitee_email": "teammate@test.com"
  }' | jq
```

**Save the `invite_id` from the response.**

**List pending invitations:**
```bash
curl http://127.0.0.1:8001/v1/invitations \
  -H "Authorization: Bearer YOUR_API_TOKEN" | jq
```

### 5. Resend Invitation

```bash
curl -X POST http://127.0.0.1:8001/v1/invitations/INVITE_ID/resend \
  -H "Authorization: Bearer YOUR_API_TOKEN" | jq
```

### 6. Accept Invitation (Public Endpoint)

```bash
curl -X POST http://127.0.0.1:8001/v1/invitations/INVITE_ID/accept | jq
```

**Expected response:**
```json
{
  "tenant_id": "...",
  "tenant_name": "Test Company",
  "invitee_email": "teammate@test.com",
  "message": "Invitation accepted! You can now register with this tenant."
}
```

### 7. Revoke Invitation

```bash
curl -X DELETE http://127.0.0.1:8001/v1/invitations/INVITE_ID \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### 8. Register Admin Tenant

**Create admin tenant for testing:**
```bash
curl -X POST http://127.0.0.1:8001/v1/tenants/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin",
    "owner_email": "admin@dyocense.com",
    "plan_tier": "platinum",
    "metadata": {}
  }' | jq
```

**Important:** The tenant_id should be "admin" for admin access. If it's not, update your .env:
```bash
ADMIN_TENANT_ID=<actual_tenant_id_from_response>
```

### 9. Admin Dashboard - List All Tenants

```bash
curl http://127.0.0.1:8001/v1/admin/tenants?limit=50&skip=0 \
  -H "Authorization: Bearer ADMIN_API_TOKEN" | jq
```

### 10. Admin Dashboard - Change Tenant Plan

```bash
curl -X PUT "http://127.0.0.1:8001/v1/admin/tenants/TENANT_ID/plan?plan_tier=gold" \
  -H "Authorization: Bearer ADMIN_API_TOKEN" | jq
```

### 11. Admin Dashboard - View Analytics

```bash
curl "http://127.0.0.1:8001/v1/admin/analytics?days=30" \
  -H "Authorization: Bearer ADMIN_API_TOKEN" | jq
```

### 12. Trial Enforcement

**Manual enforcement for specific tenant:**
```bash
curl -X POST http://127.0.0.1:8001/v1/trial/enforce \
  -H "Authorization: Bearer YOUR_API_TOKEN" | jq
```

**Admin: Enforce all expired trials:**
```bash
curl -X POST http://127.0.0.1:8001/v1/trial/enforce-all \
  -H "Authorization: Bearer ADMIN_API_TOKEN" | jq
```

### 13. Record Analytics Event

```bash
curl -X POST http://127.0.0.1:8001/v1/analytics/events \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "page_view",
    "payload": {
      "page": "/home",
      "duration": 5000
    }
  }' | jq
```

### 14. Billing Portal

```bash
curl http://127.0.0.1:8001/v1/billing/portal \
  -H "Authorization: Bearer YOUR_API_TOKEN" | jq
```

## UI Testing

### 1. Start the UI

```bash
cd apps/ui
npm run dev
```

Open http://localhost:5173

### 2. Purchase Flow

1. Click "Buy" or go to `/buy`
2. Select a plan (Silver for trial testing)
3. Enter organization details
4. Complete purchase
5. Note the success screen with:
   - Tenant ID
   - API Token
   - "Go to Login" button

### 3. Login Flow

1. Click "Go to Login"
2. Credentials should be pre-filled (tenant ID and email)
3. Enter password (if user registered) or use API token login
4. Should land on Home page

### 4. Invite Teammates (UI)

1. On Home page (create mode), scroll to "Invite teammate" card
2. Enter teammate email
3. Click "Send invite"
4. See success message with copyable accept link
5. Invite appears in pending list with Resend/Revoke buttons

### 5. Test Resend/Revoke

1. Click "Resend" on a pending invite
2. See success message
3. Click "Revoke" on a pending invite
4. Invite should disappear from list

### 6. Accept Invitation Flow

1. Copy the accept link from invite creation
2. Open in new browser/incognito window
3. Should see acceptance confirmation with tenant info
4. Click "Go to Login"
5. Login page pre-filled with tenant and email

### 7. Admin Dashboard (UI)

**Prerequisites:** Sign in as admin tenant

1. Look for "Admin" link in top navigation (Shield icon)
2. Click "Admin" → view dashboard
3. See analytics summary cards
4. See tenant list with search/filter
5. Change a tenant's plan using dropdown
6. Test pagination (if many tenants)

### 8. Accept Invite Page

1. Visit `/accept-invite/INVITE_ID`
2. See acceptance confirmation
3. See tenant details
4. Click buttons to test navigation

## Monitoring Background Jobs

### Watch Logs

```bash
# In the terminal running uvicorn, watch for:
# "Starting background tasks..."
# "Running trial enforcement job..."
# "Trial enforcement complete: X tenants downgraded"
```

### Force Trial Check (for testing)

Since background job runs every 24 hours, you can:

1. **Manually trigger enforcement:**
```bash
curl -X POST http://127.0.0.1:8001/v1/trial/enforce-all \
  -H "Authorization: Bearer ADMIN_API_TOKEN" | jq
```

2. **Or modify the sleep interval in code temporarily:**
```python
# In services/accounts/main.py, change:
await asyncio.sleep(86400)  # 24 hours
# To:
await asyncio.sleep(60)  # 1 minute (for testing)
```

## Expected Behaviors

### Invitations
- ✅ Email contains accept link (check logs if SMTP not configured)
- ✅ Accept link works without authentication
- ✅ Resend sends another email
- ✅ Revoke removes invitation from list
- ✅ Expired invitations show in list with status

### Trial Enforcement
- ✅ Silver trial tenants > 14 days old get downgraded to free
- ✅ Status changes from "trial" to "active"
- ✅ Manual enforcement works immediately
- ✅ Background job logs results every 24 hours

### Admin Dashboard
- ✅ Only admin tenant can access
- ✅ Can view all tenants
- ✅ Can change tenant plans
- ✅ Analytics show event counts
- ✅ Search and filter work

### UI
- ✅ Invite card shows on Home page (create mode)
- ✅ Success messages display after actions
- ✅ Accept link is copyable
- ✅ Admin link only shows for admin tenant
- ✅ Pre-filled login credentials work

## Troubleshooting

### No Background Job Status
```bash
# Check if service started successfully:
curl http://127.0.0.1:8001/health
```

### Invitations Not Sending Email
- Check SMTP settings in .env
- Email content logged if SMTP unavailable
- Use copyable accept link from UI instead

### Admin Access Denied
- Verify ADMIN_TENANT_ID in .env matches your admin tenant
- Check Authorization header has admin token

### MongoDB Errors
```bash
# Ensure Docker Compose services running:
docker-compose ps
```

### UI Not Connecting
- Verify VITE_DYOCENSE_BASE_URL in .env
- Check backend running on correct port
- Look for CORS errors in browser console

## Success Criteria

- [x] Can register tenant with trial
- [x] Can invite teammates
- [x] Can resend/revoke invitations
- [x] Accept link works and routes to login
- [x] Admin can view all tenants
- [x] Admin can change tenant plans
- [x] Trial enforcement runs in background
- [x] Health endpoint reports job status
- [x] UI displays all features correctly
- [x] No errors in console/logs

## Next Steps

Once testing is complete:

1. **Configure SMTP** for real email sending
2. **Set up MongoDB** persistence (if using in-memory)
3. **Deploy** to staging environment
4. **Add monitoring** for background jobs
5. **Integrate Stripe** for billing portal
6. **Add notification emails** for trial expiration warnings
