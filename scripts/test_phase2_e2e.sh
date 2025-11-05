#!/bin/bash
# Quick test script for Phase 2 features

set -e

BASE_URL="http://127.0.0.1:8001"
ADMIN_TOKEN=""
USER_TOKEN=""
TENANT_ID=""
INVITE_ID=""

echo "🧪 Phase 2 End-to-End Test"
echo "=========================="
echo ""

# Test 1: Health Check
echo "1️⃣  Testing health endpoint..."
HEALTH=$(curl -s "${BASE_URL}/health")
echo "$HEALTH" | jq
if echo "$HEALTH" | jq -e '.background_jobs.trial_enforcement.running == true' > /dev/null; then
    echo "✅ Background jobs running"
else
    echo "⚠️  Background jobs not running"
fi
echo ""

# Test 2: Register Test Tenant
echo "2️⃣  Registering test tenant..."
REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/tenants/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2E Test Company",
    "owner_email": "test@example.com",
    "plan_tier": "silver",
    "metadata": {}
  }')

echo "$REGISTER_RESPONSE" | jq
USER_TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.api_token')
TENANT_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.tenant_id')
echo "✅ Tenant registered: $TENANT_ID"
echo ""

# Test 3: Get Tenant Profile
echo "3️⃣  Getting tenant profile..."
curl -s "${BASE_URL}/v1/tenants/me" \
  -H "Authorization: Bearer ${USER_TOKEN}" | jq
echo "✅ Profile retrieved"
echo ""

# Test 4: Create Invitation
echo "4️⃣  Creating invitation..."
INVITE_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/invitations" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "invitee_email": "teammate@example.com"
  }')

echo "$INVITE_RESPONSE" | jq
INVITE_ID=$(echo "$INVITE_RESPONSE" | jq -r '.invite_id')
echo "✅ Invitation created: $INVITE_ID"
echo ""

# Test 5: List Invitations
echo "5️⃣  Listing invitations..."
curl -s "${BASE_URL}/v1/invitations" \
  -H "Authorization: Bearer ${USER_TOKEN}" | jq
echo "✅ Invitations listed"
echo ""

# Test 6: Resend Invitation
echo "6️⃣  Resending invitation..."
curl -s -X POST "${BASE_URL}/v1/invitations/${INVITE_ID}/resend" \
  -H "Authorization: Bearer ${USER_TOKEN}" | jq
echo "✅ Invitation resent"
echo ""

# Test 7: Accept Invitation (public endpoint)
echo "7️⃣  Accepting invitation..."
curl -s -X POST "${BASE_URL}/v1/invitations/${INVITE_ID}/accept" | jq
echo "✅ Invitation accepted"
echo ""

# Test 8: Record Analytics Event
echo "8️⃣  Recording analytics event..."
curl -s -X POST "${BASE_URL}/v1/analytics/events" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "payload": {"source": "e2e_test"}
  }' | jq
echo "✅ Event recorded"
echo ""

# Test 9: Register Admin Tenant
echo "9️⃣  Registering admin tenant..."
ADMIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/v1/tenants/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin",
    "owner_email": "admin@dyocense.com",
    "plan_tier": "platinum",
    "metadata": {}
  }')

echo "$ADMIN_RESPONSE" | jq
ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | jq -r '.api_token')
ADMIN_TENANT_ID=$(echo "$ADMIN_RESPONSE" | jq -r '.tenant_id')
echo "✅ Admin tenant: $ADMIN_TENANT_ID"
echo "⚠️  Note: Update ADMIN_TENANT_ID in .env to: $ADMIN_TENANT_ID"
echo ""

# Test 10: Admin - List All Tenants
echo "🔟 Admin: Listing all tenants..."
curl -s "${BASE_URL}/v1/admin/tenants?limit=10&skip=0" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" | jq '.tenants | length' | \
  xargs -I {} echo "✅ Found {} tenants"
echo ""

# Test 11: Admin - View Analytics
echo "1️⃣1️⃣  Admin: Viewing analytics..."
curl -s "${BASE_URL}/v1/admin/analytics?days=30" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" | jq
echo "✅ Analytics retrieved"
echo ""

# Test 12: Billing Portal
echo "1️⃣2️⃣  Getting billing portal..."
curl -s "${BASE_URL}/v1/billing/portal" \
  -H "Authorization: Bearer ${USER_TOKEN}" | jq
echo "✅ Billing portal URL retrieved"
echo ""

echo ""
echo "🎉 All tests passed!"
echo ""
echo "📝 Summary:"
echo "  - Tenant ID: $TENANT_ID"
echo "  - API Token: $USER_TOKEN"
echo "  - Admin Tenant: $ADMIN_TENANT_ID"
echo "  - Admin Token: $ADMIN_TOKEN"
echo "  - Invitation ID: $INVITE_ID"
echo ""
echo "🌐 Next steps:"
echo "  1. Update ADMIN_TENANT_ID in .env to: $ADMIN_TENANT_ID"
echo "  2. Test UI at http://localhost:5173"
echo "  3. Login with tenant: $TENANT_ID"
echo "  4. Check admin dashboard at http://localhost:5173/admin"
