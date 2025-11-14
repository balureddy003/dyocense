# Beta-Ready Functional Narratives

**Purpose:** Define and validate the 5 core user journeys that must work flawlessly for beta launch.

**Target:** SMB owners (non-technical) who want AI-powered business insights without complexity.

**Beta Success Criteria:** Each narrative must complete without errors, provide clear value, and feel intuitive.

---

## 📋 Core Functional Narratives

### 🎯 Narrative 1: Onboarding & First Value (0-5 minutes)

**User Story:** *"As a new SMB owner, I want to get started quickly and see what Dyocense can do for my business."*

**Flow:**

1. **Landing Page** → User reads value proposition, clicks "Try the pilot"
2. **Signup** → Enters email, password, selects "Pilot" plan (free 14-day trial)
3. **Email Verification** → Clicks magic link in inbox
4. **Welcome Wizard** → 3-step flow:
   - **Step 1:** Business profile (industry, size, current challenges)
   - **Step 2:** Preview value (see what metrics they'll track)
   - **Step 3:** Choose path: "Connect my data" or "Explore with sample data"
5. **Sample Workspace** → If they choose sample data:
   - Auto-creates "Sample Workspace" with demo inventory/sales data
   - Shows health score (65/100) with breakdown
   - Displays first goal: "Improve inventory turnover by 15%"
6. **First Win** → Dashboard shows:
   - 3 actionable insights from sample data
   - 1 agent recommendation ready to review
   - Health score trending chart

**Success Criteria:**

- ✅ Signup to first insight: < 5 minutes
- ✅ No errors in console/backend logs
- ✅ User sees personalized content (industry-specific)
- ✅ Health score is meaningful (not placeholder)
- ✅ At least 1 actionable recommendation

**Current Status:**

- ✅ Signup/login working (JWT auth)
- ✅ Welcome wizard implemented
- ⚠️ Sample workspace creation (needs testing)
- ⚠️ Health score calculation (needs real logic)
- ❌ Industry-specific insights (generic currently)

---

### 🔌 Narrative 2: Connect Real Data (5-15 minutes)

**User Story:** *"As an SMB owner, I want to connect my business data so Dyocense can analyze my actual metrics."*

**Flow:**

1. **Connectors Page** → User sees available integrations:
   - ERPNext (for inventory, orders, suppliers)
   - CSV upload (for custom data)
   - QuickBooks (coming soon)
2. **Choose ERPNext** → Clicks "Connect ERPNext"
3. **Credentials Entry** → Enters:
   - ERPNext URL
   - API Key
   - API Secret
4. **Test Connection** → Click "Test Connection"
   - Green checkmark appears: "Connected successfully"
   - Shows preview: "Found 243 SKUs, 89 suppliers, 1,247 orders"
5. **Data Sync** → Click "Start Sync"
   - Progress indicator: "Syncing inventory... 50%"
   - Agent copilot message: *"I found 15 slow-moving items and 3 stock-outs. Want me to analyze?"*
6. **Health Score Update** → After sync:
   - Score recalculates: 72/100 → 68/100
   - Alert: "Inventory health dropped (-4) due to stock-outs"
7. **First Real Insight** → Agent shows:
   - "You have $8,500 tied up in slow-moving inventory"
   - "3 items are out of stock, risking $2,100 in lost sales"

**Alternative: CSV Upload**

1. Click "Upload CSV" → Drag & drop `sales_2024.csv`
2. Column mapping: Dyocense auto-detects `date`, `product`, `revenue`, `quantity`
3. Preview shows 10 rows → Click "Import"
4. Agent acknowledges: *"I imported 365 sales records. Your best month was July ($42K). Want forecasts?"*

**Success Criteria:**

- ✅ ERPNext connector tests connection successfully
- ✅ Data preview shows accurate counts
- ✅ CSV upload handles 1000+ rows without timeout
- ✅ Health score updates based on real data
- ✅ Agent provides context-aware insights
- ✅ No credentials stored in plain text

**Current Status:**

- ✅ Connectors UI implemented
- ✅ ERPNext backend connector working
- ✅ CSV upload endpoint exists
- ⚠️ Data preview needs refinement
- ⚠️ Health score recalculation logic (partial)
- ❌ Agent contextual responses (needs improvement)

---

### 🎯 Narrative 3: Create Goal & Track Progress (10-20 minutes)

**User Story:** *"As an SMB owner, I want to set a business goal and track my progress toward it."*

**Flow:**

1. **Goals Page** → User clicks "+ New Goal"
2. **Goal Wizard** → AI-assisted goal creation:
   - **Auto-suggestion:** "Based on your inventory data, you could reduce carrying costs by 12%"
   - **Or manual:** User types "Increase revenue by 20%"
3. **Goal Details:**
   - Title: "Increase revenue by 20%"
   - Timeline: 6 months
   - Current baseline: $25K/month (auto-detected from data)
   - Target: $30K/month
4. **AI Breaks Down Goal** → Agent creates sub-tasks:
   - Launch loyalty program (5 hours)
   - Run Facebook ads campaign (3 hours)
   - Optimize pricing on top 10 products (2 hours)
   - Improve checkout conversion (4 hours)
5. **Assign Owners** → User assigns:
   - "Launch loyalty program" → Marketing Lead
   - "Facebook ads" → Self
6. **Track Progress** → Week by week:
   - Week 1: Revenue = $26K (+4% toward goal)
   - Progress bar: 20% complete
   - Alert: "Loyalty program task overdue by 2 days"
7. **Version History** → User can:
   - See what changed (timeline adjusted from 6 to 8 months)
   - Compare baseline vs. current
   - Export progress report (PDF)

**Success Criteria:**

- ✅ Goal creation < 2 minutes with AI assist
- ✅ Baseline auto-detected from connected data
- ✅ Sub-tasks are actionable and realistic
- ✅ Progress updates automatically from data syncs
- ✅ Version history shows meaningful diffs
- ✅ Export generates professional PDF report

**Current Status:**

- ✅ Goals UI implemented
- ✅ AI goal suggestions working
- ✅ Version history tracking
- ⚠️ Baseline auto-detection (needs data context)
- ⚠️ Progress auto-update (manual currently)
- ❌ PDF export (not implemented)

---

### 🤖 Narrative 4: Run Agent Analysis (5-10 minutes)

**User Story:** *"As an SMB owner, I want an AI agent to analyze my data and give me actionable recommendations."*

**Flow:**

1. **Agents Page** → User sees available agents:
   - **Inventory Optimizer** (requires ERPNext)
   - **Revenue Forecaster** (requires sales data)
   - **Customer Retention** (requires CRM data)
2. **Select Agent** → Click "Inventory Optimizer"
3. **Agent Card** → Shows:
   - Description: "Find slow-moving items, predict stock-outs, optimize reorder points"
   - Requirements: ✅ ERPNext connected
   - Estimated run time: 30 seconds
4. **Launch Agent** → Click "Run Analysis"
5. **Agent Thinking** → Real-time updates:
   - "Analyzing 243 SKUs across 12 categories..."
   - "Calculating turnover ratios..."
   - "Identifying slow movers (< 2 turns/year)..."
6. **Results Display** → Agent shows:
   - **15 slow-moving items** (total value: $8,500)
   - **3 stock-outs** (potential lost sales: $2,100/week)
   - **Recommended actions:**
     - Discount slow movers 20% to clear inventory
     - Reorder 3 items immediately (with quantities)
     - Adjust reorder points for 8 products
7. **Download Report** → Click "Download Thinking"
   - PDF with full analysis, reasoning, and action plan
8. **Share Results** → Click "Share"
   - Generates shareable link for team members

**Success Criteria:**

- ✅ Agent runs without errors
- ✅ Results displayed < 60 seconds
- ✅ Recommendations are specific (not generic)
- ✅ Thinking log shows transparent reasoning
- ✅ PDF export includes all details
- ✅ Share link works (no auth required for view-only)

**Current Status:**

- ✅ Agents UI implemented
- ✅ Backend agent orchestration working
- ✅ Real-time status updates (WebSocket)
- ✅ Download thinking/report feature
- ⚠️ Agent recommendations quality (needs tuning)
- ❌ Share link generation (not implemented)

---

### 📊 Narrative 5: Prove Impact with Evidence (5-10 minutes)

**User Story:** *"As an SMB owner, I want to export audit-ready evidence of decisions and their outcomes."*

**Flow:**

1. **Executor Page** → User navigates to execution HUD
2. **Select Template** → Choose "Inventory Optimization"
3. **Run Evidence Engines:**
   - **Correlation Analysis** → Click "Find Correlations"
     - Results: "Marketing spend correlates 0.78 with revenue (7-day lag)"
   - **What-If Scenarios** → Click "Run What-If"
     - Input: "Increase marketing budget by 20%"
     - Output: "Projected revenue increase: +$4.2K/month (R² = 0.85)"
   - **Driver Analysis** → Click "Find Drivers"
     - Results: "Top 3 drivers of revenue: repeat customers (42%), avg order value (31%), conversion rate (18%)"
4. **Granger Causality** → Click "Test Granger"
   - Hypothesis: "Email campaigns cause revenue increases"
   - Result: "✅ Significant causal relationship (p < 0.01)"
5. **Evidence Graph** → Visualizes:
   - All correlations, drivers, and causal links
   - Color-coded by strength
6. **Export Audit Trail** → Click "Export Evidence"
   - Downloads comprehensive JSON/PDF with:
     - All analysis runs (timestamps, parameters, results)
     - Statistical summaries
     - Visualizations
     - Shareable compliance-ready report

**Success Criteria:**

- ✅ All 4 evidence engines run successfully
- ✅ Results displayed with statistical confidence
- ✅ Evidence graph is interactive and clear
- ✅ Export contains all necessary audit details
- ✅ Performance: < 5 seconds per analysis
- ✅ No data leakage (tenant isolation verified)

**Current Status:**

- ✅ Evidence engines implemented (4 endpoints)
- ✅ 54 tests passing
- ✅ Prometheus metrics instrumented
- ⚠️ Evidence graph visualization (basic)
- ⚠️ Export format (JSON only, needs PDF)
- ❌ Statistical confidence intervals (not shown)

---

## 🧪 Beta Testing Checklist

### Pre-Beta Validation (Before inviting users)

**Infrastructure:**

- [ ] Prometheus collecting metrics (fix YAML error)
- [ ] Grafana dashboards imported and working
- [ ] Loki centralized logging configured
- [ ] Database backups scheduled
- [ ] SSL/TLS certificates configured
- [ ] Production passwords updated (.env)

**Functional:**

- [ ] All 5 narratives tested end-to-end
- [ ] No console errors in browser
- [ ] No 500 errors in backend logs
- [ ] Email verification working
- [ ] Password reset flow working
- [ ] Data connectors stable (ERPNext + CSV)

**Performance:**

- [ ] Signup to first insight < 5 min
- [ ] Agent analysis completes < 60 sec
- [ ] Evidence engine runs < 5 sec each
- [ ] Dashboard loads < 2 sec
- [ ] No memory leaks (sustained load test)

**Security:**

- [ ] RLS policies enabled (tenant isolation)
- [ ] JWT tokens expire after 24 hours
- [ ] Connector credentials encrypted
- [ ] CORS restricted (no wildcards in production)
- [ ] SQL injection tests pass
- [ ] Rate limiting configured

---

## 🎯 Beta Launch Plan (Week 12)

### Day 1-2: Onboard 10 Beta Users

**Target Profile:**

- SMB owners (retail, restaurants, e-commerce)
- 5-50 employees
- Currently using spreadsheets or basic tools
- Willing to connect real data

**Onboarding Process:**

1. Send personalized invite email with signup link
2. Schedule 30-minute kickoff call:
   - Show them around the platform
   - Help connect first data source
   - Create their first goal together
3. Provide support Slack channel (respond < 1 hour)

### Day 3-4: Monitor & Support

**Metrics to Track:**

- Login frequency (target: 3+ logins/week)
- Feature usage (which narratives are used most?)
- Error rates (should be < 1%)
- Support ticket volume
- Time to first value (target: < 5 min)

**Proactive Support:**

- Daily check-ins via Slack
- Fix critical bugs within 4 hours
- Weekly feedback calls (15 min each)

### Day 5: Gather Feedback

**Survey Questions:**

1. What problem were you trying to solve?
2. Did Dyocense help? How?
3. What was confusing or frustrating?
4. What feature would make this 10x better?
5. Would you pay $79/month for this? Why/why not?

**Success Metrics:**

- NPS score > 40
- 8/10 users actively engaged
- 5+ feature requests (shows engagement)
- 0 critical bugs
- 2+ success stories (testimonials)

---

## 🚀 Next Actions (Priority Order)

### 🔴 Critical (Do Now)

1. **Fix Prometheus YAML error** → Unblock observability
2. **Test all 5 narratives end-to-end** → Validate beta readiness
3. **Update production passwords** → Security hardening
4. **Configure SSL/TLS** → Required for production

### 🟡 High Priority (This Week)

5. **Improve health score calculation** → Use real data, not placeholders
6. **Enhance agent recommendations** → Industry-specific, not generic
7. **Add PDF export for goals/evidence** → Audit-ready reports
8. **Import Grafana dashboards** → Operational visibility
9. **Configure centralized logging** → Debugging + compliance

### 🟢 Medium Priority (Before Beta)

10. **Share link generation** → Team collaboration
11. **Evidence graph visualization** → Interactive, clear
12. **Statistical confidence intervals** → Trust in results
13. **Email templates** → Professional onboarding
14. **Database backup automation** → Data safety

---

## 📊 Expected Beta Outcomes

**Week 1:**

- 10 users onboarded
- 5+ connected real data sources
- 3+ goals created
- 10+ agent runs executed

**Week 2:**

- 30+ logins (average 3 per user)
- 2+ success stories captured
- 10+ improvement suggestions
- < 5 critical bugs reported

**Week 3-4:**

- 8/10 users still actively engaged
- 1-2 users willing to be case studies
- Feature roadmap prioritized from feedback
- Decision: proceed to paid launch or iterate

---

## 🎓 User Success Stories (Template)

### Template

**Business:** [Company Name], [Industry]  
**Challenge:** [What problem they had]  
**Solution:** [How they used Dyocense]  
**Result:** [Quantifiable outcome]  
**Quote:** *"[Testimonial from owner]"*

### Example

**Business:** TechFix Repairs, Electronics Repair  
**Challenge:** Slow-moving inventory tying up $12K in cash  
**Solution:** Used Inventory Optimizer agent to identify 18 slow movers, ran discount campaign  
**Result:** Cleared $9,200 in inventory in 3 weeks, reinvested in fast movers  
**Quote:** *"I didn't realize how much cash was sitting on shelves until Dyocense showed me. The agent's recommendations paid for itself in the first week."*

---

**Document Owner:** Product Team  
**Last Updated:** November 14, 2025  
**Review Cadence:** Weekly during beta, then monthly  
**Feedback:** <beta-feedback@dyocense.com>
