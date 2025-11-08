# End-to-End Functional Gaps Analysis

**Focus:** SMB-First Design - Simple, Smooth, Low Learning Curve  
**Date:** November 7, 2025  
**Goal:** Identify and fix all critical gaps for production-ready SMB platform

---

## 🎯 Executive Summary

### Current State Assessment

- ✅ **Backend:** 12 microservices unified in kernel, multi-agent system functional
- ✅ **Frontend:** React + TypeScript UI with inline data flows
- ⚠️ **Integration:** Several critical gaps in UI ↔ Backend flow
- ❌ **SMB Experience:** Too complex, missing guided flows, no onboarding

### Critical Path to Production

1. **Phase 1 (This Week):** Fix UI ↔ Backend integration gaps
2. **Phase 2 (Next Week):** Simplify SMB UX with guided flows
3. **Phase 3 (Week 3):** Add authentication, billing, monitoring

---

## 🔴 CRITICAL GAPS - Must Fix for Beta Launch

### Backend Agent Findings

#### GAP-B1: Dependencies Installation Incomplete ⚠️ BLOCKING

**Status:** CRITICAL - Pip install hanging on langchain version resolution  
**Impact:** Cannot start kernel service  
**Root Cause:** `requirements-dev.txt` has conflicting langchain version constraints

**Current State:**

```
langchain>=0.1.0,<0.2
langchain-openai>=0.0.5
langchain-core>=0.1.0,<0.2
```

**Issue:** Pip is backtracking through 60+ langchain-openai versions trying to find compatible set

**Solution:**

```
# Pin to known compatible versions
langchain==0.1.20
langchain-openai==0.1.6  
langchain-core==0.1.53
langgraph==0.0.40
```

**Action:** Update requirements-dev.txt with pinned versions

---

#### GAP-B2: Backend Service Not Running ⚠️ BLOCKING

**Status:** CRITICAL - No backend process running  
**Impact:** UI has no API to connect to  
**Evidence:** `ps aux | grep uvicorn` returns empty

**Solution Steps:**

1. Fix dependencies (GAP-B1)
2. Set environment variables (.env file missing)
3. Start kernel: `PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001`

**Missing .env Configuration:**

```bash
# Required for SMB mode
MONGO_URI=mongodb://localhost:27017/dyocense
ALLOW_ANONYMOUS=true  # For testing without Keycloak
LLM_PROVIDER=openai   # or ollama for local
OPENAI_API_KEY=sk-...  # If using OpenAI
```

---

#### GAP-B3: No Data Persistence Layer ❌ HIGH

**Status:** MongoDB not deployed/configured  
**Impact:** All data lost on restart, no evidence graph persistence  
**Current:** Services have MongoDB code but no connection string

**Solution:**

1. Deploy MongoDB via Docker: `docker run -d -p 27017:27017 mongo:7`
2. Set MONGO_URI in .env
3. Or use MongoDB Atlas free tier for cloud option

---

#### GAP-B4: Policy & Diagnostician Are Stubs ⚠️ MEDIUM

**Status:** Services return mock data  
**Impact:** No real constraint checking, no infeasibility diagnosis

**Policy Service (services/policy/main.py):**

- Currently returns hardcoded `{"allowed": true}`
- Needs OPA integration for real policy evaluation

**Diagnostician Service (services/diagnostician/main.py):**

- Returns canned relaxation suggestions
- Needs conflict detection algorithms

**Priority:** P1 (not blocking beta, but needed for v1.0)

---

#### GAP-B5: Missing Redis for Caching/Rate Limiting ⚠️ HIGH

**Status:** No caching layer, no rate limiting  
**Impact:** Poor performance, no protection from abuse

**Solution:**

1. Deploy Redis: `docker run -d -p 6379:6379 redis:7-alpine`
2. Add redis client to requirements: `redis>=5.0,<6`
3. Implement rate limiting middleware in kernel

---

#### GAP-B6: No Background Job Queue ⚠️ MEDIUM

**Status:** Orchestrator runs jobs in-process  
**Impact:** Long-running optimization blocks API requests

**Current:** services/orchestrator/main.py runs jobs synchronously  
**Needed:** Celery or RQ for background processing

**Solution:**

```bash
# Add to requirements
celery>=5.3,<6
redis>=5.0,<6  # Celery broker

# Update orchestrator to use Celery tasks
```

---

#### GAP-B7: No File Storage (MinIO/S3) ❌ HIGH

**Status:** CSV/Excel uploads have nowhere to store files  
**Impact:** Cannot persist uploaded data files

**Solution:**

1. Deploy MinIO: `docker run -d -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"`
2. Add boto3 configuration (already in requirements)
3. Update data_ingest package to use MinIO

---

### Frontend Agent Findings

#### GAP-F1: No .env File in apps/ui ⚠️ BLOCKING

**Status:** CRITICAL - UI doesn't know backend URL  
**Impact:** All API calls fail with CORS/connection errors

**Current:** Only `.env.example` exists  
**Evidence:** `apps/ui/.env.example` has config but no `.env`

**Solution:**

```bash
cd apps/ui
cp .env.example .env
# Edit .env:
VITE_DYOCENSE_BASE_URL=http://localhost:8001
VITE_ADMIN_TENANT_ID=admin
VITE_KEYCLOAK_URL=http://localhost:8080  # Optional for SMB mode
```

---

#### GAP-F2: Login Flow Requires Keycloak ⚠️ HIGH

**Status:** SMB mode should work without Keycloak  
**Impact:** Cannot test without complex enterprise auth setup

**Current:** apps/ui/src/pages/LoginPage.tsx requires Keycloak  
**Issue:** No "Quick Start" mode for SMBs

**Solution:**
Add simple email-based auth for SMB mode:

- Email + Password (no Keycloak)
- Store JWT in localStorage
- Backend `ALLOW_ANONYMOUS=true` for dev/testing

**Priority:** P0 - Critical for SMB onboarding

---

#### GAP-F3: Multi-Agent Endpoint Not Connected ⚠️ MEDIUM

**Status:** Code exists but never tested end-to-end  
**Impact:** Cannot use sophisticated multi-agent planning

**Location:** `apps/ui/src/components/AgentAssistant.tsx` lines 1600-1665  
**Issue:**

- `/v1/chat/multi-agent` endpoint exists in backend
- Frontend has code to call it
- Never tested because backend not running

**Test Needed:**

1. Start backend
2. Test complex goal: "Reduce inventory costs by 15% while maintaining 95% service level"
3. Verify 4 agents execute in sequence

---

#### GAP-F4: Inline Data Upload Not Functional ❌ HIGH

**Status:** UI shows upload component but backend has no storage  
**Impact:** Cannot upload CSV/Excel files for inventory, sales data

**Components:**

- `InlineDataUploader.tsx` - UI exists
- `InlineConnectorSelector.tsx` - UI exists
- Backend storage (MinIO) - MISSING (see GAP-B7)

**Flow Broken:**

1. User uploads CSV ❌ No file storage
2. Backend should save to MinIO ❌ Not configured
3. Compiler should reference file ❌ No persistence

---

#### GAP-F5: No Guided Onboarding Flow ❌ CRITICAL for SMB

**Status:** Users dropped into complex dashboard  
**Impact:** High learning curve, SMBs get lost immediately

**Current:** After login → dashboard with no guidance  
**Needed:** Progressive onboarding wizard

**Proposed Flow:**

```
Step 1: Welcome + Role Selection
  "I'm a restaurant owner" → Pre-configure for restaurants
  "I'm a retail store owner" → Pre-configure for retail

Step 2: First Goal Input
  "What do you want to optimize?"
  - Reduce inventory costs
  - Improve staff scheduling
  - Increase profit margins
  [Show examples/templates]

Step 3: Quick Data Connection
  "Connect your data (optional)"
  - Upload a CSV
  - Connect to Google Sheets
  - Connect to Square/Shopify
  [Skip for now - use sample data]

Step 4: Get First Result
  Run optimization with sample data
  Show immediate value
  
Step 5: Invite Team (optional)
  Collaborate with staff
```

**Priority:** P0 - Make or break for SMBs

---

#### GAP-F6: Dashboard Too Complex ❌ HIGH

**Status:** Shows run history, evidence graph, technical details  
**Impact:** Overwhelms non-technical SMB users

**Current:** `apps/ui/src/pages/DashboardPage.tsx`

- Shows JSON payloads
- Uses technical terminology
- No business-friendly summaries

**Needed:** SMB-friendly dashboard

- "Your Savings This Month: $2,450"
- "Inventory Optimized: ✅ 3 times"
- "Next Action: Review supplier orders"

**Priority:** P0 - Core SMB experience

---

#### GAP-F7: No Sample Data / Quick Start ❌ CRITICAL for SMB

**Status:** Users must upload real data before seeing value  
**Impact:** High friction, cannot try before committing

**Solution:** Pre-loaded sample scenarios

- Restaurant: Sample menu, inventory, sales data
- Retail: Sample products, sales, supplier data
- "Try It Now" button → Instant results with fake data

**Examples in `examples/` folder exist but not integrated:**

- `restaurant_inventory.csv`
- `restaurant_menu.csv`
- `sample_demand_data.csv`

**Priority:** P0 - Remove all friction for SMB trial

---

#### GAP-F8: Error Messages Too Technical ⚠️ MEDIUM

**Status:** Shows stack traces, API errors  
**Impact:** Confuses non-technical users

**Example:**

```
Current: "Request failed: 500 - Internal Server Error"
Better: "Oops! We couldn't process that. Try again or contact support."
```

**Solution:** Friendly error boundary component

---

#### GAP-F9: No Mobile Responsiveness ⚠️ MEDIUM

**Status:** Desktop-only layout  
**Impact:** SMB owners often use tablets/phones

**Evidence:** No mobile breakpoints in many components  
**Priority:** P1 (not blocking beta, but important for SMBs)

---

## 🟡 INTEGRATION GAPS - UI ↔ Backend Coordination

### GAP-I1: API Contract Mismatch ⚠️ HIGH

**Status:** Frontend expects different response shape than backend returns

**Compiler Endpoint:**

- Frontend sends: `{goal: string, context: {...}}`
- Backend `/v1/compile` expects: `{goal: string, context?: {...}, archetype_id?: string}`
- Works but archetype_id never used

**Multi-Agent Endpoint:**

- Frontend expects: `{response, goal_analysis, data_analysis, model_results, recommendations}`
- Backend returns exactly this ✅
- BUT: Never tested end-to-end

**Solution:** API contract tests needed

---

### GAP-I2: Authentication Flow Broken ❌ CRITICAL

**Status:** Frontend sends bearer token, backend requires it, but no token exists

**Frontend (lib/config.ts):**

```typescript
export function getAuthHeaders() {
  const token = localStorage.getItem("auth_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}
```

**Backend (packages/kernel_common/auth.py):**

```python
ALLOW_ANONYMOUS = os.getenv("ALLOW_ANONYMOUS", "false").lower() == "true"
if not ALLOW_ANONYMOUS:
    # Requires bearer token
```

**Issue:** No login flow generates valid token for SMB mode

**Solution:**

1. Set `ALLOW_ANONYMOUS=true` for SMB mode (immediate fix)
2. Implement simple email auth for production

---

### GAP-I3: CORS Configuration Missing ⚠️ BLOCKING

**Status:** Browser blocks API calls due to CORS  
**Impact:** UI cannot call backend even when both running

**Backend needs:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Location:** services/kernel/main.py (probably missing)

---

### GAP-I4: Data Flow Not Validated ❌ HIGH

**Status:** No end-to-end test of complete flow

**Expected Flow:**

```
1. User enters goal in chat
2. Frontend calls /v1/chat (or /v1/chat/multi-agent)
3. Chat service calls compiler
4. Compiler generates OPS JSON
5. Orchestrator calls forecast → policy → optimise → explain
6. Evidence logged to MongoDB
7. Response returned to UI
8. UI parses markers [SHOW_CONNECTORS:], [SHOW_UPLOADER:]
9. User uploads CSV or connects data
10. Re-run with real data
11. Show results in business-friendly format
```

**Broken Points:**

- Step 9: No file storage (GAP-B7, GAP-F4)
- Step 11: Technical dashboard (GAP-F6)
- Auth blocks everything (GAP-I2)

---

### GAP-I5: No Health Checks / Service Discovery ⚠️ MEDIUM

**Status:** UI doesn't know if backend is up  
**Impact:** Silent failures, bad UX

**Solution:**

- Add `/health` endpoint to kernel
- Frontend pings on load
- Show "Connecting..." or "Backend Unavailable" banner

---

## 🟢 SMB UX IMPROVEMENT GAPS - Simplification Needed

### GAP-U1: No Role-Based Simplification ❌ CRITICAL

**Status:** Same UI for technical users and SMB owners  
**Impact:** SMBs see irrelevant features

**Solution:** User roles

- **SMB Owner:** Simple mode (hide JSON, evidence graph, technical terms)
- **Data Analyst:** Advanced mode (show everything)
- **Developer:** API mode (docs, SDK, curl examples)

---

### GAP-U2: No Industry-Specific Templates ❌ HIGH

**Status:** Generic "enter a goal" interface  
**Impact:** SMBs don't know what to ask for

**Solution:** Template library

- Restaurant: "Optimize menu pricing", "Reduce food waste", "Schedule staff"
- Retail: "Minimize stockouts", "Optimize reorder points", "Seasonal planning"
- Services: "Optimize appointment scheduling", "Balance workload"

**Location:** Could leverage existing archetypes in `packages/archetypes/`

---

### GAP-U3: No Proactive Guidance ❌ MEDIUM

**Status:** User must know what to do next  
**Impact:** Low engagement after first use

**Solution:** Next action suggestions

- "📊 Your inventory data is 2 weeks old. Upload fresh data?"
- "💡 Tip: Connect your POS system for automatic updates"
- "🎯 You saved $500 last month. Try staff scheduling next?"

---

### GAP-U4: No Visual Results ⚠️ MEDIUM

**Status:** Text-only responses  
**Impact:** Hard to understand optimization impact

**Solution:** Charts and graphs

- Before/After comparison
- Savings over time
- Inventory level visualization

**Suggested Library:** Recharts or Chart.js (lightweight)

---

### GAP-U5: No Collaboration Features ⚠️ LOW

**Status:** Single-user experience  
**Impact:** SMBs often have partners/managers who need access

**Needed:**

- Team invitations (backend has this in Phase 2!)
- Shared goals
- Comments on decisions
- @mentions

**Note:** Backend already has invitation system (services/accounts/main.py) - just need UI!

---

## 📋 PRIORITY MATRIX

### P0 - Must Fix This Week (Blocking Beta)

| Gap ID | Description | Owner | Effort |
|--------|-------------|-------|--------|
| GAP-B1 | Fix dependencies (pin langchain versions) | Backend | 30 min |
| GAP-B2 | Start kernel service with .env | Backend | 1 hour |
| GAP-F1 | Create apps/ui/.env file | Frontend | 15 min |
| GAP-I2 | Set ALLOW_ANONYMOUS=true for SMB mode | Backend | 15 min |
| GAP-I3 | Add CORS middleware | Backend | 30 min |
| GAP-F2 | Add simple login (email/password) | Both | 4 hours |
| GAP-F5 | Build onboarding wizard (MVP) | Frontend | 8 hours |
| GAP-F7 | Integrate sample data | Both | 4 hours |

**Total: ~2-3 days of work**

---

### P1 - Next Week (Beta Polish)

| Gap ID | Description | Owner | Effort |
|--------|-------------|-------|--------|
| GAP-B3 | Deploy MongoDB | Backend | 2 hours |
| GAP-B5 | Deploy Redis | Backend | 2 hours |
| GAP-B7 | Deploy MinIO for file storage | Backend | 3 hours |
| GAP-F4 | Connect file upload to MinIO | Both | 4 hours |
| GAP-F6 | Rebuild dashboard (SMB-friendly) | Frontend | 8 hours |
| GAP-U2 | Add industry templates | Frontend | 6 hours |
| GAP-I4 | End-to-end integration tests | Both | 4 hours |

**Total: ~4-5 days of work**

---

### P2 - Week 3+ (Production Hardening)

| Gap ID | Description | Owner | Effort |
|--------|-------------|-------|--------|
| GAP-B4 | Implement real Policy/Diagnostician | Backend | 2 weeks |
| GAP-B6 | Add Celery for background jobs | Backend | 1 week |
| GAP-F9 | Mobile responsiveness | Frontend | 1 week |
| GAP-U3 | Proactive guidance system | Both | 1 week |
| GAP-U4 | Add charts/visualizations | Frontend | 1 week |
| GAP-U5 | Team collaboration UI | Frontend | 1 week |

---

## 🚀 IMMEDIATE ACTION PLAN

### Day 1 (Today) - Get It Running

**Goal:** Backend + Frontend both running, can make API calls

**Backend Agent Tasks:**

1. ✅ Update requirements-dev.txt with pinned langchain versions
2. ✅ Create .env file at project root with SMB config
3. ✅ Add CORS middleware to kernel service
4. ✅ Install dependencies: `pip install -r requirements-dev.txt`
5. ✅ Start kernel: `PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001`

**Frontend Agent Tasks:**

1. ✅ Create apps/ui/.env from .env.example
2. ✅ Install dependencies: `cd apps/ui && npm install`
3. ✅ Start dev server: `npm run dev`
4. ✅ Test health check: Open browser to <http://localhost:5173>

**Coordination Point:** Once both running, test API call from browser console

---

### Day 2 - Simple Auth + Sample Data

**Goal:** User can "Quick Start" with sample data, no Keycloak needed

**Backend Agent:**

1. Deploy MongoDB locally: `docker run -d -p 27017:27017 mongo:7`
2. Create sample data loader script
3. Add /v1/auth/simple-login endpoint (email + password → JWT)

**Frontend Agent:**

1. Create SimpleLoginPage (no Keycloak)
2. Add "Try Sample Data" button to AgentAssistant
3. Show sample restaurant scenario with pre-filled data

**Coordination:** Simple auth endpoint contract

---

### Day 3-4 - Onboarding Wizard

**Goal:** New user sees guided wizard, gets first result in 2 minutes

**Frontend Agent:**

1. Create OnboardingWizard component (5 steps)
2. Industry selection → Template selection → Sample data → Run → Results
3. Skip button for power users

**Backend Agent:**

1. Ensure sample data returns fast results (<5 seconds)
2. Create /v1/archetypes/templates endpoint (industry-specific)

**Coordination:** Template structure, sample data format

---

### Day 5 - Polish + Test

**Goal:** Beta-ready for 10 test users

**Both Agents:**

1. End-to-end testing of complete flow
2. Error handling (friendly messages)
3. Loading states
4. Fix any discovered bugs

---

## 📊 SUCCESS METRICS

### Technical Metrics

- ✅ Backend starts in <30 seconds
- ✅ Frontend loads in <2 seconds
- ✅ API response time <1 second (90th percentile)
- ✅ Zero CORS errors
- ✅ Zero authentication failures in SMB mode

### SMB UX Metrics

- ✅ User gets first result in <2 minutes (with sample data)
- ✅ Onboarding completion rate >80%
- ✅ Dashboard comprehension (user testing: understand results without help)
- ✅ Mobile usability score >70 (Lighthouse)

### Business Metrics

- ✅ 10 beta users complete onboarding
- ✅ At least 5 users run optimization with their own data
- ✅ At least 2 users invite team members
- ✅ Zero critical bugs reported

---

## 🔧 TECHNICAL COORDINATION POINTS

### Shared Interfaces

#### 1. Authentication

**Contract:**

```typescript
// Frontend → Backend
POST /v1/auth/simple-login
Request: { email: string, password: string }
Response: { token: string, user: { id, email, tenant_id, role } }

// Stored in localStorage as "auth_token"
// Sent as "Authorization: Bearer {token}" in all requests
```

**Backend Implementation:** services/accounts/main.py (extend existing)  
**Frontend Implementation:** New SimpleLoginPage.tsx

---

#### 2. Sample Data

**Contract:**

```typescript
// Frontend → Backend
GET /v1/samples?industry=restaurant&scenario=inventory
Response: {
  scenario_id: string,
  name: string,
  description: string,
  sample_goal: string,
  sample_data: {
    products: [...],
    demand_forecast: [...],
    constraints: {...}
  }
}

// Then use sample_data in regular /v1/chat or /v1/runs
```

**Backend Implementation:** New services/samples/ service  
**Frontend Implementation:** SampleDataSelector.tsx

---

#### 3. Template Library

**Contract:**

```typescript
// Frontend → Backend
GET /v1/templates?industry=restaurant
Response: {
  templates: [
    {
      id: "inventory_optimization",
      name: "Reduce Inventory Costs",
      description: "Minimize holding costs while avoiding stockouts",
      industry: "restaurant",
      difficulty: "beginner",
      estimated_savings: "$500-2000/month",
      sample_goal: "Reduce my inventory costs by 15%..."
    }
  ]
}
```

**Backend Implementation:** Extend services/marketplace/main.py  
**Frontend Implementation:** TemplateLibrary.tsx

---

#### 4. Onboarding State

**Contract:**

```typescript
// Track user onboarding progress
POST /v1/users/me/onboarding
Request: { step: number, completed: boolean }

GET /v1/users/me/onboarding
Response: { current_step: number, completed_steps: [1,2,3] }
```

**Backend Implementation:** services/accounts/main.py (add onboarding_state field)  
**Frontend Implementation:** OnboardingWizard.tsx

---

## 🎯 COORDINATION PROTOCOL

### Daily Sync Points

1. **Morning:** Review overnight progress, unblock dependencies
2. **Mid-day:** Integration point check (APIs ready? UI ready?)
3. **End of day:** Demo working features, identify next day's tasks

### Integration Testing Schedule

- **Day 1 EOD:** Backend health check + Frontend can call /health
- **Day 2 EOD:** Login flow + Sample data loading
- **Day 3 EOD:** Onboarding wizard step 1-3
- **Day 4 EOD:** Complete onboarding flow + First optimization result
- **Day 5:** Full end-to-end test with real user scenarios

### Git Workflow

- **Backend Branch:** `feat/smb-backend-integration`
- **Frontend Branch:** `feat/smb-ui-simplification`
- **Integration Branch:** `feat/smb-e2e` (merge both when integration points ready)

### Communication

- **Blockers:** Post immediately in shared doc/chat
- **API Changes:** Notify other agent before committing
- **Questions:** Tag with [BACKEND] or [FRONTEND] prefix

---

## 📝 NOTES & DECISIONS

### Why Pinning Langchain Versions?

LangChain ecosystem moves fast, breaking changes common. Pinning ensures reproducible builds.

### Why ALLOW_ANONYMOUS for SMB Mode?

Keycloak is enterprise complexity. SMBs need "sign up with email" → immediate value. We can add Keycloak as Platform tier upgrade.

### Why Sample Data First?

Reduces friction. User sees value in 2 minutes, then commits to uploading real data. Classic SaaS onboarding pattern.

### Why Separate Onboarding Wizard?

First-time user experience is different from power user. Wizard is training wheels that can be skipped later.

### Why MongoDB Instead of PostgreSQL?

Flexibility for unstructured evidence data, OPS JSON storage, audit trails. Easier for rapid iteration.

---

## 🔄 FEEDBACK LOOP

After Day 5 (Beta Ready):

1. Deploy to staging environment
2. Recruit 10 SMB beta testers (restaurants, retail)
3. User testing sessions (watch them use it)
4. Collect feedback via survey + interviews
5. Iterate on top 5 pain points
6. Repeat weekly until NPS >40

---

## ✅ DEFINITION OF DONE

### For Each Gap

- [ ] Code implemented and tested locally
- [ ] Integration test passes
- [ ] Error handling added
- [ ] Loading states implemented (frontend)
- [ ] Logged for observability (backend)
- [ ] User-facing documentation updated (if needed)
- [ ] Merged to integration branch

### For Beta Launch

- [ ] All P0 gaps closed
- [ ] 10 beta users signed up
- [ ] User can complete onboarding in <2 minutes
- [ ] Sample data works for restaurant + retail
- [ ] Simple login works (no Keycloak needed)
- [ ] Dashboard shows business-friendly results
- [ ] Mobile view functional (basic)
- [ ] Error messages are friendly
- [ ] Backend deployed and stable
- [ ] MongoDB + Redis deployed
- [ ] Monitoring/alerting basic setup

---

## 🚨 RISK REGISTER

### Risk 1: Dependencies Still Won't Install

**Mitigation:** Use Docker with pre-built image, or drop langchain entirely for beta (use simpler LLM client)

### Risk 2: Backend Performance Too Slow

**Mitigation:** Use sample data with cached results for demo, optimize later

### Risk 3: SMB Users Still Confused

**Mitigation:** Add video tutorial, more hand-holding in wizard, offer 1:1 onboarding calls

### Risk 4: Integration Takes Longer Than Expected

**Mitigation:** Build frontend stubs that work with mock data, parallelize work

---

## 📞 ESCALATION PATH

### If Blocked >4 Hours

1. Post in shared channel with [BLOCKED] tag
2. Schedule quick sync call
3. Consider workaround/temporary solution

### If Behind Schedule

1. Cut scope (move P1 to P2)
2. Focus on one industry (restaurant only) for beta
3. Use more mock data, less real integration

### If Technical Showstopper

1. Assess severity (blocks beta? blocks single feature?)
2. If blocks beta: All hands on deck, fix immediately
3. If blocks feature: Defer to P2, find alternative

---

**END OF DOCUMENT**

*This is a living document. Update as gaps are discovered/resolved.*
