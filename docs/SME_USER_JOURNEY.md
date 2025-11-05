# Small Business Owner Journey - End-to-End Flow

## Vision Alignment

Dyocense is the **Decision Intelligence Platform for Small Businesses** - providing the missing Decision Kernel that turns AI insights into optimal, explainable decisions without requiring data science expertise.

### Core Value Proposition
- **For SMEs**: Get optimal decisions for inventory, staffing, and supply chain
- **No Expertise Needed**: Pre-built archetypes and guided playbooks
- **AI-Powered**: LLMs + Forecasting + Operational Research combined
- **Explainable**: Full audit trails and compliance built-in

---

## User Journey Flow

### 1. Discovery (Landing Page)

**Scenario**: Small business owner searching for supply chain optimization tools

**Experience**:
```
┌─────────────────────────────────────────────┐
│         🌟 Dyocense Landing Page           │
├─────────────────────────────────────────────┤
│                                             │
│  "Turn AI Insights Into Optimal Decisions" │
│                                             │
│  🎯 Decision Intelligence Platform          │
│  📦 Pre-built Supply Chain Archetypes       │
│  🔒 Enterprise-Grade Compliance             │
│                                             │
│  [🚀 Start 7-Day Free Trial]               │
│  [Start Free Forever]                       │
│                                             │
│  "No credit card required"                  │
└─────────────────────────────────────────────┘
```

**Features Section**:
- **AI-Powered Decision Intelligence** - LLMs + Forecasting + OR
- **Built for Small Businesses** - No data science needed
- **Enterprise-Grade Compliance** - Audit trails included

**Use Cases**:
- 📈 Inventory Optimization
- 👥 Workforce Planning
- 🔄 Supply Chain Planning

**Pricing Preview**:
```
┌──────────┬──────────────┬─────────┐
│   FREE   │ SILVER TRIAL │  GOLD   │
├──────────┼──────────────┼─────────┤
│   $0     │  $0 / 7 days │  $499   │
│ forever  │ Then $149/mo │  /month │
├──────────┼──────────────┼─────────┤
│ 1 proj   │  5 projects  │ 20 proj │
│ 3 books  │  25 books    │ 150 bks │
│ 2 users  │  15 users    │ 75 user │
└──────────┴──────────────┴─────────┘
```

---

### 2. Trial Signup (No Credit Card)

**User Action**: Clicks "Start 7-Day Free Trial"

**Flow**:
1. **Redirect**: `/buy?plan=trial`
2. **Form Shows**:
   ```
   ┌─────────────────────────────────────┐
   │  Start Your 7-Day Free Trial       │
   │  (Silver Plan - Full Access)        │
   ├─────────────────────────────────────┤
   │  Organization Name: [________]      │
   │  Email: [________@______]           │
   │                                     │
   │  [✓] Start Free Trial               │
   │                                     │
   │  Then $149/month after 7 days      │
   │  Cancel anytime • No credit card    │
   └─────────────────────────────────────┘
   ```

3. **Backend**: `POST /v1/tenants/register`
   ```json
   {
     "name": "Acme Corp",
     "owner_email": "owner@acme.com",
     "plan_tier": "silver",
     "metadata": {
       "trial_started_at": "2025-11-05T10:00:00Z",
       "trial_ends_at": "2025-11-12T10:00:00Z"
     }
   }
   ```

4. **Welcome Email Sent**:
   ```
   Subject: Welcome to Dyocense - 7-Day Free Trial

   Hi,

   Welcome to Dyocense! Your 7-day free trial of the Silver plan
   is now active for 'Acme Corp'.

   Tenant ID: acme-019df5
   Temporary Password: ********

   Click here to complete your account setup:
   http://localhost:5173/login?tenant=acme-019df5&email=owner@acme.com

   Your trial includes:
   ✓ 5 active projects
   ✓ 25 AI playbooks
   ✓ 15 team members
   ✓ Business-hours support

   Trial ends: November 12, 2025

   After trial, choose to upgrade ($149/month) or continue with Free plan.

   Get started: [Complete Registration]
   ```

---

### 3. First-Time Registration

**User Action**: Clicks login link from email

**Experience**:
```
┌─────────────────────────────────────────┐
│  Welcome to Dyocense                   │
├─────────────────────────────────────────┤
│  👋 Use the temporary password from    │
│     your welcome email to register     │
├─────────────────────────────────────────┤
│  Tenant ID: acme-019df5 (pre-filled)  │
│  Email: owner@acme.com (pre-filled)    │
│                                         │
│  [Register] ← Click this toggle        │
│                                         │
│  Full Name: [____________]              │
│  Create Password: [********]            │
│  Temporary Password: [********]         │
│                                         │
│  [Create Account]                       │
└─────────────────────────────────────────┘
```

**Backend**: `POST /v1/users/register`
- Verifies temporary password from tenant metadata
- Creates user account
- Clears temporary password
- Returns success

**Result**: User can now login with permanent credentials

---

### 4. First Login & Onboarding

**Experience**:
```
┌─────────────────────────────────────────┐
│  Sign In                                │
├─────────────────────────────────────────┤
│  Tenant ID: acme-019df5                 │
│  Email: owner@acme.com                  │
│  Password: [********]                   │
│                                         │
│  [Sign In]                              │
└─────────────────────────────────────────┘
```

**After Login**: Redirect to `/profile` (Profile Setup Page)
```
┌─────────────────────────────────────────┐
│  Welcome! Let's set up your profile    │
├─────────────────────────────────────────┤
│  Business Name: [____________]          │
│  Industry: [Retail ▼]                   │
│  Team Size: [1-10 ▼]                    │
│  Primary Goal: [Inventory Opt ▼]        │
│  Timezone: [America/New_York ▼]         │
│                                         │
│  [Continue to Dashboard] →              │
└─────────────────────────────────────────┘
```

---

### 5. Explore Platform (Trial Period)

**Dashboard View** (`/home`):
```
┌────────────────────────────────────────────────────────┐
│  Dyocense    Control Tower  Playbooks  Marketplace    │
│              [🎉 Trial: 6 days left]  [Settings] [⚙️] │
├────────────────────────────────────────────────────────┤
│                                                        │
│  🎯 Quick Actions                                      │
│  ┌───────────────┬───────────────┬──────────────┐    │
│  │ New Playbook  │ Upload Data   │ Invite Team  │    │
│  └───────────────┴───────────────┴──────────────┘    │
│                                                        │
│  📊 Recent Projects                                    │
│  • Inventory Optimization (Active)                    │
│  • Staffing Schedule (Draft)                          │
│                                                        │
│  💡 Getting Started Tips                               │
│  ✓ Profile setup complete                             │
│  → Upload your first dataset                          │
│  → Create a playbook from template                    │
│  → Invite team members                                │
└────────────────────────────────────────────────────────┘
```

**Key Features Available**:
- ✅ Create up to 5 projects
- ✅ Use 25 AI playbooks
- ✅ Invite up to 15 team members
- ✅ Business-hours support
- ✅ Export evidence/history

---

### 6. Trial Reminder (Day 5)

**Email Sent**:
```
Subject: Your Dyocense Trial Ends in 2 Days

Hi owner@acme.com,

Your 7-day free trial of Dyocense Silver plan ends in 2 days.

What happens next?

UPGRADE ($149/month):
✓ Keep all 5 projects
✓ Keep 25 playbooks
✓ Keep 15 team members
✓ Business-hours support

[Upgrade Now] → Settings

FREE PLAN:
• 1 project (you'll choose which to keep)
• 3 playbooks
• 2 team members
• Community support

[Learn More]

Questions? Reply to this email.
```

---

### 7. Settings & Subscription Management

**User Action**: Navigates to Settings (`/settings`)

**Experience**:
```
┌─────────────────────────────────────────────────────┐
│  Settings                                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  👤 Profile                                         │
│  Business: Acme Corp                                │
│  Tenant ID: acme-019df5                             │
│  Email: owner@acme.com                              │
│                                                     │
├─────────────────────────────────────────────────────┤
│  💳 Subscription                                    │
│  ┌─────────────────────────────────────────────┐   │
│  │  Current Plan: SILVER                       │   │
│  │  🎉 Trial active • 2 days remaining         │   │
│  │                                             │   │
│  │         [⬆️ Upgrade Plan]                   │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ⚠️ Trial ending soon!                              │
│  Your trial ends in 2 days. Upgrade now to          │
│  continue with full access.                         │
│                                                     │
│  [Upgrade to Silver - $149/month]                   │
│                                                     │
├─────────────────────────────────────────────────────┤
│  🔑 API Token (Developer Access)                    │
│  [Show API Token]                                   │
└─────────────────────────────────────────────────────┘
```

**After Upgrade Click**: Redirects to `/buy` with upgrade flow

---

### 8. Upgrade Decision

**Option A: Upgrade to Paid**

```
POST /v1/tenants/me/subscription
{
  "plan_tier": "silver"
}
```

**Result**:
- Trial converted to paid subscription
- No data loss
- All features remain active
- Billing starts

---

**Option B: Let Trial Expire**

**Day 8 (Automatic)**:
- Background job runs: `trial_enforcement_job()`
- Detects expired trial
- Executes: `enforce_trial_for_tenant(tenant_id)`
- **Auto-downgrade**: `plan_tier = "free"`

**Email Sent**:
```
Subject: Your Dyocense Trial Has Ended

Hi owner@acme.com,

Your 7-day trial of Silver plan has ended.

You've been moved to the FREE plan:
• 1 active project (others archived)
• 3 playbooks (others archived)
• 2 team members

Your data is safe. Upgrade anytime to restore full access.

[Upgrade to Silver - $149/month]
```

**User Experience on Next Login**:
```
┌─────────────────────────────────────────┐
│  ℹ️ Your trial has ended                │
│                                         │
│  You're now on the Free plan.          │
│  Upgrade to restore full access.        │
│                                         │
│  [View Upgrade Options]                 │
└─────────────────────────────────────────┘
```

---

### 9. Free Forever Option

**Alternative Path**: User clicks "Start Free Forever" on landing page

**Flow**:
1. `/buy?plan=free`
2. Same registration process
3. Starts with Free tier immediately
4. No trial period
5. Can upgrade anytime from Settings

**Limits**:
- 1 project
- 3 playbooks
- 2 members
- Community support

**Upgrade Path**: Always available in Settings

---

## Technical Implementation

### Backend Components

**1. Tenant Registration** (`/v1/tenants/register`)
```python
def register_new_tenant(payload):
    # Create tenant with selected plan
    tenant = register_tenant(
        name=payload.name,
        owner_email=payload.owner_email,
        plan_tier=payload.plan_tier,  # "free" or "silver"
        metadata={
            "trial_started_at": now() if silver else None,
            "trial_ends_at": now() + 7days if silver else None,
            "temporary_password": keycloak_temp_pass
        }
    )
    
    # Send welcome email (NO API token)
    send_email(
        to=owner_email,
        subject="Welcome to Dyocense",
        body=f"Tenant: {tenant_id}\nTemp Password: {temp_pass}"
    )
    
    return tenant
```

**2. Background Trial Enforcement** (runs every 24h)
```python
async def trial_enforcement_job():
    while background_tasks_running:
        # Find expired Silver trials
        expired_trials = find_expired_trials()
        
        for tenant in expired_trials:
            # Downgrade to free
            enforce_trial_for_tenant(tenant.tenant_id)
            
            # Send notification email
            send_trial_expired_email(tenant.owner_email)
        
        await asyncio.sleep(86400)  # 24 hours
```

**3. Subscription Management** (`/v1/tenants/me/subscription`)
```python
@app.put("/v1/tenants/me/subscription")
def update_subscription(payload, identity):
    tenant = update_tenant_plan(
        tenant_id=identity["tenant_id"],
        plan_tier=payload.plan_tier
    )
    
    # Clear trial metadata if upgrading
    if payload.plan_tier != "free":
        tenant.metadata.pop("trial_ends_at", None)
    
    return tenant
```

### Frontend Components

**1. Landing Page** (`/`)
- Hero with clear value prop
- Use cases section
- Pricing comparison
- CTAs: "Start Trial" vs "Start Free"

**2. Purchase Flow** (`/buy?plan=trial|free`)
- Pre-selected plan from URL param
- Organization details form
- Email with temp password
- Success page with next steps

**3. Settings** (`/settings`)
- Profile display
- **Subscription section** with:
  - Current plan display
  - Trial countdown (if applicable)
  - Upgrade button
  - Trial expiration warning
- API token management

---

## Email Templates

### 1. Welcome Email (Trial)
```
Subject: Welcome to Dyocense - Your 7-Day Free Trial Starts Now

Hi [Name],

🎉 Welcome to Dyocense!

Your 7-day free trial of the Silver plan is now active for '[Org Name]'.

GET STARTED:
Tenant ID: [tenant-id]
Temporary Password: [temp-pass]

👉 Complete your setup: [Login Link]

WHAT'S INCLUDED IN YOUR TRIAL:
✓ 5 active projects
✓ 25 AI playbooks
✓ 15 team members
✓ Business-hours support
✓ Full export capabilities

Trial ends: [Date]

After your trial, you can:
• Upgrade to Silver ($149/month)
• Continue with Free plan (limited features)

Questions? Hit reply!

The Dyocense Team
```

### 2. Trial Reminder (Day 5)
```
Subject: 2 Days Left in Your Dyocense Trial

Hi [Name],

Your Dyocense trial ends in 2 days (on [Date]).

KEEP YOUR FULL ACCESS - Upgrade to Silver ($149/month):
✓ All 5 projects stay active
✓ All 25 playbooks preserved
✓ Team of 15 continues
✓ Priority support

[Upgrade Now →]

OR CONTINUE FREE:
• 1 project (you choose which)
• 3 playbooks
• 2 team members

All your data is safe either way!

Questions? We're here to help.

[Upgrade] | [Learn More]
```

### 3. Trial Expired
```
Subject: Your Dyocense Trial Has Ended - You're Now on Free Plan

Hi [Name],

Your 7-day Silver trial has ended.

GOOD NEWS:
✓ Your data is safe and archived
✓ You're now on our Free plan
✓ Upgrade anytime to restore full access

FREE PLAN:
• 1 active project
• 3 playbooks
• 2 team members
• Community support

RESTORE FULL ACCESS:
Upgrade to Silver ($149/month) to restore:
• All 5 projects
• All 25 playbooks
• 15 team members
• Business-hours support

[Upgrade Now →]

Need help? Reply to this email.
```

---

## Success Metrics

### Conversion Funnel
```
Landing Page Visit
    ↓ (30% click CTA)
Trial Signup
    ↓ (80% complete registration)
First Login
    ↓ (60% complete profile)
Active Usage (7 days)
    ↓ (40% convert to paid)
Paying Customer
```

### Key Metrics to Track
- **Landing → Trial**: Signup conversion rate
- **Trial → Registration**: Completion rate
- **Registration → Login**: Activation rate
- **Trial → Paid**: Upgrade conversion rate
- **Trial → Free**: Downgrade rate
- **Free → Paid**: Upgrade-from-free rate

---

## Future Enhancements

### Phase 2 Improvements
1. **Credit Card Capture** (optional) during trial
2. **In-App Upgrade Flow** with Stripe integration
3. **Usage Analytics** dashboard in Settings
4. **Team Collaboration** features preview
5. **Marketplace** for solution packs

### Phase 3 Features
1. **Multi-tier trials** (Gold trial for enterprises)
2. **Referral program** (get free month)
3. **Annual billing** (save 20%)
4. **Custom enterprise plans**
5. **White-label options**

---

## Summary

This end-to-end flow ensures:

✅ **Frictionless Discovery** - Clear value prop on landing page
✅ **No-Risk Trial** - 7 days free, no credit card needed
✅ **Easy Registration** - Temporary password, single-use
✅ **Guided Onboarding** - Profile setup, getting started tips
✅ **Clear Visibility** - Trial countdown in Settings
✅ **Graceful Downgrade** - Automatic free tier conversion
✅ **Easy Upgrades** - One-click from Settings
✅ **Secure API Access** - Tokens behind authentication

**The SME Journey**: Land → Trial → Explore → Upgrade (or Free) → Grow

---

## Phased Implementation Roadmap (SMB → Enterprise)

This roadmap builds on Phase 1 (Keycloak + SMB onboarding) and sequences capabilities so the platform scales from small businesses to enterprises while staying contract-first and observable. Each phase lists scope, key changes, and acceptance criteria.

### Phase 1 — DONE: Identity, Trial Signup, SMB Purchase Flow

- Delivered per `PHASE1_IMPLEMENTATION.md` and `PHASE1_DEPLOYMENT.md`.
- Outcome: Tenants can sign up, get a realm (when configured), and access the shell UI.

Acceptance criteria (met):

- Realm-per-tenant (optional) provisioning with temp password and forced reset.
- `/buy` wizard live; onboarding details retrievable; graceful fallback without Keycloak.

---

### Phase 2 — Business Profile + Goal Suggestions (Templates-first)

Scope (user stories):

- As an owner, when I select a plan, I provide my business type, size, locations, seasonality, and objectives.
- Based on my profile, I see recommended goals (e.g., “Forecast orders,” “Optimize inventory,” “Staffing schedule”).

Changes:

- Contracts: Add JSON-Schemas for BusinessProfile and GoalTemplate selection (under `docs/schemas/`).
- Backend: New endpoints in `services/accounts` and/or `services/kernel`:
    - `POST /v1/profile` (create/update business profile)
    - `GET /v1/goals/recommendations?profile_id=…`
- UI: Extend `PurchasePage` and `ProfileSetupPage` to capture business profile and show goal suggestions; add a new “Suggested Playbooks” section on `/home`.
- Data: Seed a starter catalog of goal templates per vertical (restaurant, retail, services) under `docs/examples/` and `packages/archetypes/`.

Acceptance criteria:

- Upon purchase or first login, user completes profile, then sees at least 3 recommended goals.
- Recommendations are deterministic from seeded templates; type-safe contracts validated.

---

### Phase 3 — Forecasting MVP + Playbooks (Inventory, Staffing)

Scope:

- As an owner, I can connect CSV/Sheets, select a forecasting playbook, and get daily/weekly forecasts.
- I can create an Inventory or Staffing playbook from a template with minimal inputs.

Changes:

- Services: Wire `services/forecast` into `services/orchestrator` and `/v1/forecast`; enable dataset ingestion via MinIO/CSV and Google Sheets (connector stubs).
- UI: In `HomePage`, expand “Create Playbook” to include forecast-backed templates. Show forecast charts and summary in `InsightsPanel`.
- Contracts: Define `forecast.input.schema.json` and `forecast.output.schema.json`.

Acceptance criteria:

- Upload CSV or link a Google Sheet; run forecast; view point/low/high with model info.
- Create at least one playbook that consumes forecast output and renders KPIs on `/home`.

---

### Phase 4 — Optimisation + Explainability + Evidence Graph

Scope:

- As an owner, I can optimise plans (inventory order quantities, staffing schedules) and see explanations and evidence for decisions.

Changes:

- Services: `services/optimiser` (OR-Tools CBC) integrated via `services/orchestrator`; `services/explainer` for LLM-based summaries; `services/evidence` for graph capture (Neo4j CE).
- UI: `ItineraryColumn` shows decision outputs; `InsightsPanel` adds “Why this plan?” and evidence paths. Add export (SolutionPack) enhancements.
- Contracts: `ops.schema.json`, `solutionpack.schema.json`; enrich evidence event payloads (CloudEvents).

Acceptance criteria:

- Users run optimisation from a playbook; receive feasible plan with KPIs and an explanation card.
- Evidence graph node appears for each run; export includes evidence references.

---

### Phase 5 — Marketplace: Templates, Solvers, Connectors

Scope:

- As a user, I can browse and install templates and data connectors from a marketplace.

Changes:

- Services: `services/marketplace` lists catalog (archetypes, solvers, connectors) via `GET /v1/catalog`.
- Packaging: OCI bundles for templates/connectors under `packages/` and `docs/openapi/` references.
- UI: Add Marketplace route and card grid; install → config drawer (secrets via `services/accounts`).

Acceptance criteria:

- Marketplace lists at least: Inventory Optimization template, Staffing template, CSV + Google Sheets connectors.
- Install flow writes config; connector healthcheck succeeds and can read sample data.

---

### Phase 6 — Competitor Analysis (Side-by-Side Benchmarks)

Scope:

- As an owner, I can compare my KPIs to competitors/industry benchmarks and get gap-closing recommendations.

Changes:

- Data: Import public benchmark datasets; allow CSV upload for known competitor metrics.
- Services: `services/diagnostician` expands with benchmarking; recommendations surfaced in `InsightsPanel`.
- UI: Add Competitor tab with side-by-side KPI tiles and trends.

Acceptance criteria:

- Users view their KPIs vs. benchmark; get at least 3 targeted suggestions based on gaps.

---

### Phase 7 — What‑If Scenarios + Learning & Feedback

Scope:

- As an owner, I can branch scenarios (price change, demand shock), compare outcomes, and give feedback to improve future recommendations.

Changes:

- Services: `services/scenario` manages branches and diffs; `services/explainer` returns what-if summaries; feedback endpoint `/v1/feedback` captured per run.
- UI: Add “Create Scenario” flow and side-by-side diff of KPIs/constraints; thumbs-up/down with comments on recommendations.

Acceptance criteria:

- Scenario run produces differential KPIs; feedback is stored and shown on subsequent suggestions.

---

### Phase 8 — Enterprise Scale: RBAC, Multi‑Tenant Controls, Quotas

Scope:

- As an admin, I manage roles, org-level policies, quotas, and SSO.

Changes:

- Identity: Expand Keycloak roles and groups; org/project RBAC in `packages/kernel_common/auth`.
- Policy: OPA policies for resource limits; per-tenant quotas reflected in UI plan banners.
- Billing: Hooks for plan upgrades, limits enforcement (projects, playbooks, users).

Acceptance criteria:

- Role-based access applied across projects/playbooks; limits enforced with graceful UX.

---

### Phase 9 — Observability, Events, Trust & Compliance

Scope:

- Full traces/metrics/logs for Goal → Forecast → Optimise → Explain; CloudEvents on key lifecycle events; attach compliance facts.

Changes:

- Observability: OpenTelemetry tracing across services; Prometheus metrics; Loki logs.
- Events: NATS/Kafka CloudEvents; user webhooks.
- Trust: Attach a1facts-style compliance statements to runs; signed artifacts (Cosign) in CI.

Acceptance criteria:

- Each run has a trace ID; events emitted and visible; compliance facts stored and retrievable in exports.

---

### Phase 10 — SDKs, MCP Server, Community Templates

Scope:

- Ship SDKs (Python/TypeScript) and an MCP Server exposing core tools; encourage community templates.

Changes:

- SDKs: `packages/sdk-python`, `packages/sdk-typescript` add high-level helpers.
- MCP: Minimal server exposing compile/optimise/forecast tools for agent runtimes.
- Docs: Authoring guide for templates/connectors; submission to marketplace.

Acceptance criteria:
- Example notebooks/apps call the API via SDKs; MCP clients (VS Code/Claude) can invoke tools locally.

---

## Cross-Cutting Requirements

- Contract-first: Every new capability ships a JSON-Schema/OpenAPI update under `docs/openapi` and `docs/schemas`.
- Tests: Golden datasets for inventory/staffing; regression tests in `tests/` for compile/forecast/solve/explain flows.
- Security: Auth on all new endpoints; tenant isolation preserved; secrets managed centrally.
- Performance: SLOs tracked in Grafana; autoscaling via KEDA once containerised.

## Immediate Next Actions

- Implement Phase 2:

    - Schemas: `business_profile.schema.json`, `goal_template.schema.json`.
    - API: `POST /v1/profile`, `GET /v1/goals/recommendations` in `services/kernel` (routing to `services/accounts` and catalog).
    - UI: Extend `PurchasePage` and `ProfileSetupPage` to capture profile and render suggestions on `/home`.
    - Seed: Add 3 verticals (Restaurant, Retail, Services) with 3 goal templates each under `packages/archetypes/`.

Tracking: See repository issues/epics per phase; link PRs to this roadmap section for traceability.
