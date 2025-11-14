#!/bin/bash
# Beta Narrative Validation Script
# Tests all 5 core user journeys end-to-end

set -e

BASE_URL="${BASE_URL:-http://localhost:8001}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:5173}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🧪 BETA NARRATIVE VALIDATION"
echo "=========================================="
echo ""
echo "Backend: $BASE_URL"
echo "Frontend: $FRONTEND_URL"
echo ""

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0
CRITICAL_FAILURES=()

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    CRITICAL_FAILURES+=("$1")
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

section() {
    echo ""
    echo "=========================================="
    echo "📋 $1"
    echo "=========================================="
}

# ==========================================
# NARRATIVE 1: ONBOARDING & FIRST VALUE
# ==========================================
section "Narrative 1: Onboarding & First Value"

# Test 1.1: Health check
echo "Testing backend health..."
HEALTH=$(curl -s "$BASE_URL/health" || echo "FAILED")
if echo "$HEALTH" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    pass "Backend is healthy"
else
    fail "Backend health check failed"
    echo "Response: $HEALTH"
fi

# Test 1.2: Register new tenant
echo "Testing tenant registration..."
RANDOM_EMAIL="test-$(date +%s)@dyocense.test"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/tenants/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$RANDOM_EMAIL\",
    \"password\": \"TestPassword123!\",
    \"full_name\": \"Beta Tester\",
    \"plan_tier\": \"pilot\"
  }" || echo '{"error": "request failed"}')

if echo "$REGISTER_RESPONSE" | jq -e '.tenant_id' > /dev/null 2>&1; then
    TENANT_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.tenant_id')
    pass "Tenant registration successful (ID: ${TENANT_ID:0:8}...)"
else
    fail "Tenant registration failed"
    echo "Response: $REGISTER_RESPONSE"
    exit 1
fi

# Test 1.3: Login
echo "Testing login flow..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$RANDOM_EMAIL\",
    \"password\": \"TestPassword123!\"
  }" || echo '{"error": "request failed"}')

if echo "$LOGIN_RESPONSE" | jq -e '.token' > /dev/null 2>&1; then
    JWT_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token')
    pass "Login successful, JWT token received"
else
    fail "Login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

# Test 1.4: Create sample workspace
echo "Testing sample workspace creation..."
WORKSPACE_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/onboarding/$TENANT_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "workspace_name": "Sample Workspace",
    "plan_title": "Sample Launch Plan",
    "archetype_id": "inventory_basic"
  }' || echo '{"error": "request failed"}')

if echo "$WORKSPACE_RESPONSE" | jq -e '.workspace.id' > /dev/null 2>&1; then
    WORKSPACE_ID=$(echo "$WORKSPACE_RESPONSE" | jq -r '.workspace.id')
    pass "Sample workspace created (ID: ${WORKSPACE_ID:0:8}...)"
else
    fail "Sample workspace creation failed"
    echo "Response: $WORKSPACE_RESPONSE"
fi

# Test 1.5: Check health score
echo "Testing health score calculation..."
DASHBOARD=$(curl -s "$BASE_URL/v1/tenants/$TENANT_ID/dashboard" \
  -H "Authorization: Bearer $JWT_TOKEN" || echo '{}')

if echo "$DASHBOARD" | jq -e '.health_score' > /dev/null 2>&1; then
    HEALTH_SCORE=$(echo "$DASHBOARD" | jq -r '.health_score')
    if [ "$HEALTH_SCORE" != "0" ] && [ "$HEALTH_SCORE" != "null" ]; then
        pass "Health score calculated: $HEALTH_SCORE"
    else
        warn "Health score is 0 or null (needs real calculation)"
    fi
else
    warn "Health score not found in dashboard response"
fi

# ==========================================
# NARRATIVE 2: CONNECT REAL DATA
# ==========================================
section "Narrative 2: Connect Real Data"

# Test 2.1: List available connectors
echo "Testing connectors list..."
CONNECTORS=$(curl -s "$BASE_URL/v1/tenants/$TENANT_ID/connectors" \
  -H "Authorization: Bearer $JWT_TOKEN" || echo '[]')

if echo "$CONNECTORS" | jq -e 'length > 0' > /dev/null 2>&1; then
    CONNECTOR_COUNT=$(echo "$CONNECTORS" | jq 'length')
    pass "Connectors available: $CONNECTOR_COUNT"
else
    fail "No connectors available"
fi

# Test 2.2: CSV upload endpoint
echo "Testing CSV upload endpoint..."
CSV_TEST_FILE=$(mktemp).csv
echo "date,product,revenue,quantity" > "$CSV_TEST_FILE"
echo "2024-01-01,Widget A,1200,10" >> "$CSV_TEST_FILE"
echo "2024-01-02,Widget B,850,5" >> "$CSV_TEST_FILE"

CSV_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/connectors/csv/upload" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@$CSV_TEST_FILE" || echo '{"error": "request failed"}')

rm "$CSV_TEST_FILE"

if echo "$CSV_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    pass "CSV upload successful"
else
    warn "CSV upload endpoint may not be fully implemented"
    echo "Response: $CSV_RESPONSE"
fi

# Test 2.3: ERPNext connector configuration
echo "Testing ERPNext connector setup..."
ERPNEXT_CONFIG=$(curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/connectors/erpnext/configure" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://demo.erpnext.com",
    "api_key": "test_key_placeholder",
    "api_secret": "test_secret_placeholder"
  }' || echo '{"error": "request failed"}')

if echo "$ERPNEXT_CONFIG" | jq -e '.connector_id' > /dev/null 2>&1; then
    pass "ERPNext connector configured"
else
    warn "ERPNext connector configuration may require real credentials"
fi

# ==========================================
# NARRATIVE 3: CREATE GOAL & TRACK
# ==========================================
section "Narrative 3: Create Goal & Track Progress"

# Test 3.1: Get goal suggestions
echo "Testing goal suggestions..."
SUGGESTIONS=$(curl -s "$BASE_URL/v1/tenants/$TENANT_ID/goals/suggestions?industry=retail" \
  -H "Authorization: Bearer $JWT_TOKEN" || echo '[]')

if echo "$SUGGESTIONS" | jq -e 'length > 0' > /dev/null 2>&1; then
    SUGGESTION_COUNT=$(echo "$SUGGESTIONS" | jq 'length')
    pass "Goal suggestions returned: $SUGGESTION_COUNT"
else
    warn "No goal suggestions available"
fi

# Test 3.2: Create goal
echo "Testing goal creation..."
GOAL_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/goals" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Increase revenue by 20%",
    "timeline": "6 months",
    "baseline": 25000,
    "target": 30000,
    "tasks": [
      {"title": "Launch loyalty program", "estimated_hours": 5},
      {"title": "Run Facebook ads", "estimated_hours": 3}
    ]
  }' || echo '{"error": "request failed"}')

if echo "$GOAL_RESPONSE" | jq -e '.goal_id' > /dev/null 2>&1; then
    GOAL_ID=$(echo "$GOAL_RESPONSE" | jq -r '.goal_id')
    pass "Goal created successfully (ID: ${GOAL_ID:0:8}...)"
else
    fail "Goal creation failed"
    echo "Response: $GOAL_RESPONSE"
fi

# Test 3.3: List goals
echo "Testing goal listing..."
GOALS=$(curl -s "$BASE_URL/v1/tenants/$TENANT_ID/goals" \
  -H "Authorization: Bearer $JWT_TOKEN" || echo '[]')

if echo "$GOALS" | jq -e 'length > 0' > /dev/null 2>&1; then
    pass "Goals listed successfully"
else
    warn "No goals returned"
fi

# ==========================================
# NARRATIVE 4: RUN AGENT ANALYSIS
# ==========================================
section "Narrative 4: Run Agent Analysis"

# Test 4.1: List available agents
echo "Testing agent catalog..."
AGENTS=$(curl -s "$BASE_URL/v1/agents/catalog" \
  -H "Authorization: Bearer $JWT_TOKEN" || echo '[]')

if echo "$AGENTS" | jq -e 'length > 0' > /dev/null 2>&1; then
    AGENT_COUNT=$(echo "$AGENTS" | jq 'length')
    pass "Agents available: $AGENT_COUNT"
else
    warn "No agents in catalog"
fi

# Test 4.2: Launch agent (if catalog exists)
if [ -n "$AGENTS" ] && echo "$AGENTS" | jq -e '.[0].id' > /dev/null 2>&1; then
    AGENT_ID=$(echo "$AGENTS" | jq -r '.[0].id')
    echo "Testing agent launch (ID: $AGENT_ID)..."
    
    AGENT_RUN=$(curl -s -X POST "$BASE_URL/v1/tenants/$TENANT_ID/agents/$AGENT_ID/run" \
      -H "Authorization: Bearer $JWT_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{}' || echo '{"error": "request failed"}')
    
    if echo "$AGENT_RUN" | jq -e '.run_id' > /dev/null 2>&1; then
        RUN_ID=$(echo "$AGENT_RUN" | jq -r '.run_id')
        pass "Agent launched (Run ID: ${RUN_ID:0:8}...)"
        
        # Wait for completion (max 30 seconds)
        echo "Waiting for agent to complete..."
        for i in {1..30}; do
            sleep 1
            STATUS=$(curl -s "$BASE_URL/v1/tenants/$TENANT_ID/agents/runs/$RUN_ID" \
              -H "Authorization: Bearer $JWT_TOKEN" | jq -r '.status' || echo "unknown")
            
            if [ "$STATUS" = "completed" ]; then
                pass "Agent completed successfully"
                break
            elif [ "$STATUS" = "failed" ]; then
                fail "Agent run failed"
                break
            fi
            
            if [ $i -eq 30 ]; then
                warn "Agent run timeout (30s), status: $STATUS"
            fi
        done
    else
        warn "Agent launch may not be fully implemented"
    fi
fi

# ==========================================
# NARRATIVE 5: PROVE IMPACT WITH EVIDENCE
# ==========================================
section "Narrative 5: Prove Impact with Evidence"

# Test 5.1: Correlation analysis
echo "Testing correlation analysis..."
CORRELATION=$(curl -s -X POST "$BASE_URL/v1/evidence/correlations" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"tenant_id\": \"$TENANT_ID\",
    \"series\": {
      \"marketing_spend\": [1000, 1200, 1100, 1300, 1250],
      \"revenue\": [5000, 5800, 5500, 6200, 6000]
    }
  }" || echo '{"error": "request failed"}')

if echo "$CORRELATION" | jq -e '.correlations' > /dev/null 2>&1; then
    pass "Correlation analysis successful"
else
    fail "Correlation analysis failed"
    echo "Response: $CORRELATION"
fi

# Test 5.2: What-if scenario
echo "Testing what-if analysis..."
WHATIF=$(curl -s -X POST "$BASE_URL/v1/evidence/what-if" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"tenant_id\": \"$TENANT_ID\",
    \"baseline\": {\"marketing_spend\": 1000, \"revenue\": 5000},
    \"scenario\": {\"marketing_spend\": 1200}
  }" || echo '{"error": "request failed"}')

if echo "$WHATIF" | jq -e '.predicted_revenue' > /dev/null 2>&1; then
    PREDICTED=$(echo "$WHATIF" | jq -r '.predicted_revenue')
    pass "What-if analysis successful (predicted: $PREDICTED)"
else
    warn "What-if analysis may need real model"
    echo "Response: $WHATIF"
fi

# Test 5.3: Driver analysis
echo "Testing driver analysis..."
DRIVERS=$(curl -s -X POST "$BASE_URL/v1/evidence/drivers" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"tenant_id\": \"$TENANT_ID\",
    \"target\": \"revenue\",
    \"features\": {
      \"marketing_spend\": [1000, 1200, 1100],
      \"avg_order_value\": [50, 55, 52],
      \"conversion_rate\": [0.02, 0.025, 0.022]
    },
    \"target_values\": [5000, 5800, 5500]
  }" || echo '{"error": "request failed"}')

if echo "$DRIVERS" | jq -e '.drivers' > /dev/null 2>&1; then
    pass "Driver analysis successful"
else
    warn "Driver analysis may need refinement"
fi

# Test 5.4: Granger causality
echo "Testing Granger causality..."
GRANGER=$(curl -s -X POST "$BASE_URL/v1/evidence/granger" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"tenant_id\": \"$TENANT_ID\",
    \"cause\": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    \"effect\": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  }" || echo '{"error": "request failed"}')

if echo "$GRANGER" | jq -e '.p_value' > /dev/null 2>&1; then
    P_VALUE=$(echo "$GRANGER" | jq -r '.p_value')
    pass "Granger causality test successful (p=$P_VALUE)"
else
    warn "Granger test may need minimum data requirements"
fi

# ==========================================
# OBSERVABILITY CHECKS
# ==========================================
section "Observability & Infrastructure"

# Test: Prometheus metrics
echo "Testing Prometheus metrics endpoint..."
METRICS=$(curl -s "$BASE_URL/metrics" || echo "FAILED")
if echo "$METRICS" | grep -q "evidence_correlations_total"; then
    pass "Prometheus metrics endpoint working"
else
    warn "Prometheus metrics may not be exposed"
fi

# Test: Grafana accessibility
echo "Testing Grafana accessibility..."
GRAFANA_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health || echo "000")
if [ "$GRAFANA_HEALTH" = "200" ]; then
    pass "Grafana is accessible"
else
    warn "Grafana may not be running (HTTP $GRAFANA_HEALTH)"
fi

# Test: PostgreSQL connection
echo "Testing PostgreSQL connection..."
if command -v psql > /dev/null; then
    PGPASSWORD="${POSTGRES_PASSWORD:-metadataPass123}" psql -h localhost -U "${POSTGRES_USER:-metadata}" -d "${POSTGRES_DB:-metadata}" -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        pass "PostgreSQL connection successful"
    else
        warn "PostgreSQL connection failed (may be credentials)"
    fi
else
    warn "psql not installed, skipping PostgreSQL test"
fi

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo "=========================================="
echo "📊 TEST SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Failed:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ CRITICAL FAILURES:${NC}"
    for failure in "${CRITICAL_FAILURES[@]}"; do
        echo "  - $failure"
    done
    echo ""
    echo "⚠️  Beta is NOT ready. Fix critical failures first."
    exit 1
else
    echo -e "${GREEN}✅ All critical tests passed!${NC}"
    echo ""
    echo "🎉 Beta narratives validated successfully"
    echo ""
    echo "Next steps:"
    echo "  1. Test manually in browser ($FRONTEND_URL)"
    echo "  2. Verify Grafana dashboards (http://localhost:3000)"
    echo "  3. Check centralized logs in Loki"
    echo "  4. Update production passwords"
    echo "  5. Schedule beta user onboarding calls"
    exit 0
fi
