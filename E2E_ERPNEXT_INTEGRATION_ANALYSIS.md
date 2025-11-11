# End-to-End Business Owner Journey Analysis

## Dyocense Platform with ERPNext Integration

**Date**: 2025-01-11  
**Scope**: Complete user flow from signup to AI coach interaction with real ERPNext data

---

## 🎯 Executive Summary

**Status**: ⚠️ **PARTIALLY INTEGRATED** - Critical gaps identified

### What Works

✅ Email signup and verification flow  
✅ Tenant provisioning with PostgreSQL  
✅ Business profile creation  
✅ Connector infrastructure (GrandNode, Salesforce)  
✅ Goals and plans service  
✅ AI coach with rich data visualization  
✅ PostgreSQL connector_data caching layer  

### What's Missing

❌ **ERPNext connector implementation**  
❌ Tenant doesn't exist in PostgreSQL (only 'system' tenant)  
❌ Business profile → Connector → Goals integration not automated  
❌ Welcome flow doesn't persist profile to backend  

---

## 📋 Complete User Journey Map

### Phase 1: Signup & Account Creation

#### Frontend Flow

```
/signup → Signup.tsx
  ├─ Collects: email, name, business_name, intent, use_case
  ├─ POST /v1/auth/signup
  └─ Redirects to /verify?token=XXX

/verify → Verify.tsx
  ├─ POST /v1/auth/verify with token
  ├─ Receives JWT + tenant_id + workspace_id
  └─ Redirects to /welcome (first time) or /home
```

#### Backend Flow (services/accounts/main.py)

```python
POST /v1/auth/signup (Line 970)
  ├─ Validates email not already registered
  ├─ Creates verification token
  ├─ Stores in VERIFICATION_TOKENS dict
  └─ Returns token (dev) or sends email (prod)

POST /v1/auth/verify (Line 1030)
  ├─ Validates token
  ├─ register_tenant() → Creates tenant in PostgreSQL
  ├─ create_project() → Creates default workspace
  ├─ register_user() → Creates owner user
  ├─ issue_jwt() → Returns authentication token
  └─ Response: { jwt, tenant_id, workspace_id, user }
```

#### Database Impact

**Tables Written**:

- `tenants.tenants` → New tenant row
- `tenants.projects` → Default workspace
- `tenants.users` → Owner user account

**Current Issue**: ❌ In practice, only 'system' tenant exists in PostgreSQL

---

### Phase 2: Business Profile Setup

#### Frontend Flow (apps/smb/src/pages/Welcome.tsx)

```
/welcome → 3-step onboarding wizard
  Step 1: Health Score Reveal (Line 145)
    ├─ Calls getBusinessMetricsFromConnectors()
    ├─ Calculates health score (revenue, cash flow, etc.)
    └─ Animates score reveal

  Step 2: Goal Selection (Line 98)
    ├─ Presents 4 goal templates:
    │   - Grow Revenue
    │   - Improve Cash Flow
    │   - Win More Customers
    │   - Optimize Operations
    ├─ User selects or creates custom goal
    └─ Generates preview tasks

  Step 3: Plan Preview (Line 119)
    ├─ Shows 5-week action plan
    ├─ Button: "Connect your data sources" → /connectors
    └─ Button: "Complete Onboarding" → /home
```

#### Backend Flow

**Current Implementation**: ⚠️ **NONE**

```
❌ No API to save:
  - Selected goal from welcome wizard
  - Business profile (industry, size, etc.)
  - Health score baseline

⚠️ Welcome flow data lives ONLY in frontend localStorage
```

**What Should Exist**:

```python
# services/smb_gateway/main.py (MISSING)
POST /v1/tenants/{tenant_id}/profile/business
  ├─ Input: { industry, company_size, team_size, primary_goal, goals }
  ├─ Updates tenants.tenants.metadata JSONB field
  └─ Returns saved profile

POST /v1/tenants/{tenant_id}/onboarding/complete
  ├─ Creates initial goal from welcome wizard
  ├─ Marks tenant as onboarded
  └─ Triggers welcome email with next steps
```

---

### Phase 3: Connector Setup (ERPNext)

#### Frontend Flow (apps/smb/src/pages/Connectors.tsx)

```
/connectors → Connector management page
  ├─ Lists existing connectors (GET /v1/connectors)
  ├─ Button: "Add Connector" opens modal
  ├─ Preset options:
  │   - CSV Upload
  │   - Google Drive
  │   - Shopify
  │   - GrandNode
  │   ❌ ERPNext (MISSING)
  └─ Form fields based on preset
```

**Current ERPNext Gap**:

```typescript
// apps/smb/src/pages/Connectors.tsx
const presets: ConnectorPreset[] = [
  // ... existing presets
  // ❌ MISSING:
  {
    id: 'erpnext',
    label: 'ERPNext',
    description: 'Sync inventory, orders, and suppliers from ERPNext ERP',
    fields: [
      { name: 'api_url', label: 'ERPNext URL', placeholder: 'https://erp.example.com' },
      { name: 'api_key', label: 'API Key' },
      { name: 'api_secret', label: 'API Secret' }
    ]
  }
]
```

#### Backend Flow

```python
# services/connectors/routes.py (Line 230)
POST /api/connectors/sync
  ├─ Gets connector config from _connectors dict
  ├─ Calls connector-specific sync function:
  │   - sync_grandnode_data() for GrandNode
  │   - sync_salesforce_data() for Salesforce
  │   ❌ sync_erpnext_data() MISSING
  ├─ Saves data to PostgreSQL connector_data table
  └─ Returns { success, record_count, synced_at }
```

**ERPNext Connector Requirements**:

```python
# services/connectors/erpnext.py (TO CREATE)
class ERPNextConfig(BaseModel):
    api_url: str
    api_key: str
    api_secret: str
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_suppliers: bool = True

class ERPNextConnector:
    async def fetch_inventory() -> List[Dict]:
        # GET /api/resource/Item
        # Returns: [{ item_code, item_name, stock_qty, reorder_level, ... }]
    
    async def fetch_orders() -> List[Dict]:
        # GET /api/resource/Sales Order
        # Returns: [{ name, customer, grand_total, delivery_date, ... }]
    
    async def fetch_suppliers() -> List[Dict]:
        # GET /api/resource/Supplier
        # Returns: [{ name, supplier_type, payment_terms, ... }]
```

**Database Flow**:

```sql
-- After sync, data stored in:
connectors.connector_data
  ├─ tenant_id: 'cycloner ake-abc123'
  ├─ connector_id: 'erpnext_001'
  ├─ data_type: 'inventory'
  ├─ data: [{ item_code: 'PROD-A1', stock: 150, ... }, ...]
  ├─ synced_at: '2025-01-11T10:30:00Z'
  └─ record_count: 47
```

---

### Phase 4: Goal Definition

#### Frontend Flow (apps/smb/src/components/CoachSettings.tsx)

```
Settings Panel (In-chat settings)
  ├─ Goal Input Field
  ├─ Model Selection (GPT-4, Claude, etc.)
  ├─ Temperature Slider
  └─ Data Source Selection
      ├─ Lists available connectors
      ├─ Shows record counts
      └─ Enables/disables sources
```

#### Backend Flow

```python
# services/smb_gateway/main.py (Line 348)
POST /v1/tenants/{tenant_id}/goals
  ├─ Input: CreateGoalRequest
  │   - title: str
  │   - description: str
  │   - target_value: float
  │   - target_date: datetime
  │   - category: 'revenue' | 'operations' | 'customer'
  ├─ goals_service.create_goal()
  ├─ Stores in PostgreSQL (goals table)
  └─ Returns Goal object with goal_id

GET /v1/tenants/{tenant_id}/goals
  ├─ Optional filter by status
  ├─ Returns all goals for tenant
  └─ Used by coach to understand user objectives
```

**Integration Gap**: ⚠️ Goals created separately from welcome wizard goal selection

---

### Phase 5: AI Coach Interaction

#### Frontend Flow (apps/smb/src/pages/CoachV4.tsx)

```
/home → AI Coach Interface
  ├─ Chat input
  ├─ Streaming responses (SSE)
  ├─ Rich data cards (MetricsCard component)
  └─ Context from:
      ├─ User goals
      ├─ Connector data (ERPNext)
      └─ Business profile
```

#### Backend Flow

```python
# services/smb_gateway/main.py (Line 730)
POST /v1/tenants/{tenant_id}/coach/stream
  ├─ Authentication check
  ├─ Fetches connector data via _fetch_connector_data()
  │   └─ SELECT * FROM connectors.connector_data WHERE tenant_id = ?
  ├─ Builds business context:
  │   - Revenue metrics
  │   - Inventory levels
  │   - Customer data
  │   - Low stock alerts
  ├─ Calls multi_agent_coach.stream_chat()
  │   ├─ Routes to specialized agent (Strategy/Finance/Operations)
  │   ├─ LLM generates response with context
  │   └─ Adds rich_data metadata for visualizations
  └─ Streams response as SSE chunks
```

**Data Flow**:

```
ERPNext → Connector Sync → PostgreSQL connector_data
                              ↓
                    _fetch_connector_data()
                              ↓
                    Business Context Builder
                              ↓
                    AI Coach System Prompt
                              ↓
                    LLM Response with Metrics
                              ↓
                    Frontend Renders MetricsCard
```

---

## 🔍 Critical Integration Gaps

### 1. Tenant Creation Gap

**Problem**: After signup/verify, tenant should exist in PostgreSQL but only 'system' tenant found

**Root Cause**: Verify endpoint may not be creating tenant correctly, or database not persisting

**Fix Required**:

```python
# services/accounts/main.py Line 1059
def verify_email_token(payload: VerifyRequest):
    # ... existing code ...
    tenant = register_tenant(  # This should write to PostgreSQL
        name=business_name,
        owner_email=email,
        plan_tier=PlanTier.FREE
    )
    # ✅ Verify tenant written to tenants.tenants table
```

**Test**:

```sql
-- After signup, should see:
SELECT tenant_id, name, owner_email 
FROM tenants.tenants 
WHERE owner_email = 'test@cyclonerake.com';
```

---

### 2. ERPNext Connector Missing

**Problem**: No ERPNext connector implementation for CycloneRake's ERP system

**Required Files**:

1. `services/connectors/erpnext.py` - Connector implementation
2. Update `services/connectors/routes.py` - Add ERPNext sync case
3. Update `apps/smb/src/pages/Connectors.tsx` - Add ERPNext preset

**Implementation**:

```python
# services/connectors/erpnext.py
class ERPNextConfig(BaseModel):
    api_url: str  # https://erp.cyclonerake.com
    api_key: str
    api_secret: str
    sync_inventory: bool = True
    sync_orders: bool = True
    sync_suppliers: bool = True

async def sync_erpnext_data(config: ERPNextConfig) -> ERPNextData:
    async with ERPNextConnector(config) as connector:
        return await connector.sync_all()
```

---

### 3. Business Profile → Backend Persistence

**Problem**: Welcome wizard collects profile but doesn't save to backend

**Current**: Profile lives in localStorage only  
**Required**: POST endpoint to persist profile

**Implementation**:

```python
# services/smb_gateway/main.py (ADD)
@app.post("/v1/tenants/{tenant_id}/profile/business")
async def update_business_profile(
    tenant_id: str,
    profile: BusinessProfileRequest
):
    # Update tenants.tenants.metadata JSONB
    UPDATE tenants.tenants 
    SET metadata = metadata || %s::jsonb
    WHERE tenant_id = %s
```

---

### 4. Welcome Wizard → Goals Integration

**Problem**: Goal selected in welcome wizard not persisted to goals service

**Required Flow**:

```
Welcome.tsx (Step 2: Goal Selection)
  ↓
POST /v1/tenants/{tenant_id}/onboarding/complete
  {
    "selected_goal": { title, description, category },
    "health_score": 67,
    "profile": { industry, team_size }
  }
  ↓
Backend creates:
  - Goal in goals service
  - Updates tenant profile
  - Marks onboarding complete
```

---

## ✅ Production Readiness Checklist

### Immediate (P0) - Blocks ERPNext Integration

- [ ] Create tenant in PostgreSQL after signup/verify
- [ ] Create `services/connectors/erpnext.py`
- [ ] Add ERPNext to connector routes sync logic
- [ ] Add ERPNext preset to frontend Connectors.tsx
- [ ] Test ERPNext sync with real CycloneRake credentials

### High Priority (P1) - Complete Integration

- [ ] Add `POST /v1/tenants/{tenant_id}/profile/business`
- [ ] Add `POST /v1/tenants/{tenant_id}/onboarding/complete`
- [ ] Update Welcome.tsx to persist goal selection
- [ ] Verify connector_data → AI coach data flow works

### Medium Priority (P2) - UX Enhancement

- [ ] Add data freshness indicators in coach responses
- [ ] Add connector status monitoring
- [ ] Add sync history visualization
- [ ] Add low inventory alerts in coach

---

## 🧪 E2E Test Plan with ERPNext

### Test Scenario: CycloneRake Onboarding

```bash
# 1. Signup
curl -X POST http://localhost:8002/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@cyclonerake.com",
    "name": "John Doe",
    "business_name": "CycloneRake",
    "intent": "optimize_operations",
    "use_case": "Track inventory and orders from ERPNext"
  }'

# Expected: Returns verification token

# 2. Verify
curl -X POST http://localhost:8002/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{ "token": "TOKEN_FROM_STEP_1" }'

# Expected: Returns { jwt, tenant_id, workspace_id }
# Verify: SELECT * FROM tenants.tenants WHERE tenant_id = ?

# 3. Setup ERPNext Connector
curl -X POST http://localhost:8001/api/connectors/erpnext/setup \
  -H "Authorization: Bearer JWT_FROM_STEP_2" \
  -d '{
    "tenant_id": "cyclonerake-abc123",
    "user_id": "user-xyz",
    "name": "CycloneRake ERP",
    "api_url": "https://erp.cyclonerake.com",
    "api_key": "ERPNEXT_API_KEY",
    "api_secret": "ERPNEXT_API_SECRET",
    "sync_inventory": true,
    "sync_orders": true,
    "sync_suppliers": true
  }'

# Expected: Returns { success, connector_id }

# 4. Trigger First Sync
curl -X POST http://localhost:8001/api/connectors/sync \
  -H "Authorization: Bearer JWT" \
  -d '{ "connector_id": "CONNECTOR_ID_FROM_STEP_3" }'

# Expected: Syncs data to PostgreSQL
# Verify: SELECT * FROM connectors.connector_data WHERE tenant_id = 'cyclonerake-abc123'

# 5. Create Goal
curl -X POST http://localhost:8003/v1/tenants/cyclonerake-abc123/goals \
  -H "Authorization: Bearer JWT" \
  -d '{
    "title": "Optimize Inventory Turnover",
    "description": "Reduce overstock by 30% and improve turnover to 95%",
    "target_value": 95.0,
    "target_date": "2025-04-01",
    "category": "operations"
  }'

# 6. Ask AI Coach
curl -X POST http://localhost:8003/v1/tenants/cyclonerake-abc123/coach/stream \
  -H "Authorization: Bearer JWT" \
  -d '{
    "message": "What products are low in stock and need reordering?",
    "persona": "operations"
  }'

# Expected: AI coach responds with:
# - Current inventory levels from ERPNext
# - Products below reorder point
# - Supplier recommendations
# - Rich data card with metrics
```

---

## 📊 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BUSINESS OWNER JOURNEY                    │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
        ┌─────▼──────┐            ┌──────▼───────┐
        │   Signup   │            │   Verify     │
        │  (Email)   │            │  (Token)     │
        └─────┬──────┘            └──────┬───────┘
              │                           │
              │     Accounts Service      │
              │      (Port 8002)          │
              └───────────┬───────────────┘
                          │
                    ┌─────▼─────┐
                    │ PostgreSQL │
                    │  tenants   │
                    │   users    │
                    │  projects  │
                    └─────┬──────┘
                          │
              ┌───────────┴────────────┐
              │                        │
        ┌─────▼──────┐          ┌─────▼──────┐
        │  Welcome   │          │ Connectors │
        │  Wizard    │          │   Setup    │
        └─────┬──────┘          └─────┬──────┘
              │                        │
              │                   ┌────▼────────┐
              │                   │ ERPNext API │
              │                   │   Sync      │
              │                   └────┬────────┘
              │                        │
              │                  ┌─────▼───────────┐
              │                  │ connector_data  │
              │                  │ (PostgreSQL)    │
              │                  └─────┬───────────┘
              │                        │
        ┌─────▼──────┐          ┌──────▼──────┐
        │   Goals    │          │  AI Coach   │
        │  Creation  │◄─────────┤   Context   │
        └─────┬──────┘          │   Builder   │
              │                 └──────┬──────┘
              │                        │
              └────────────┬───────────┘
                           │
                     ┌─────▼─────┐
                     │ AI Coach  │
                     │ Response  │
                     │  + Rich   │
                     │   Data    │
                     └───────────┘
```

---

## 🔧 Implementation Priority

### Week 1: Foundation

1. Fix tenant creation in PostgreSQL
2. Create ERPNext connector
3. Test connector sync flow

### Week 2: Integration

1. Add business profile persistence
2. Connect welcome wizard to backend
3. Test E2E with real ERPNext

### Week 3: Polish

1. Add data freshness monitoring
2. Add connector health checks
3. Add rich error messages

---

**Generated**: 2025-01-11  
**Next Actions**: Create ERPNext connector, fix tenant provisioning
