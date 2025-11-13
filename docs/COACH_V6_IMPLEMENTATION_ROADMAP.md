# Coach V6: Fitness Dashboard Implementation Roadmap

## Executive Summary

**Decision Required:** Proceed with 2-week validation sprint before committing to full implementation.

**Investment:** $7,500 validation + $180k full implementation (if validated)

**Timeline:** 2 weeks validation + 12 weeks implementation = **14 weeks total**

**Expected ROI:** 3x pricing increase ($200 vs $75/mo) + 50% reduction in churn

---

## Phase 0: Validation Sprint (Weeks 1-2) - START HERE

### Goal

Validate that SMB owners understand and prefer the "fitness dashboard" concept over current chat interface.

### Week 1: Design & Recruit

#### Monday (Day 1)

**Product Designer:**

- [ ] Review design spec (COACH_V6_FITNESS_DASHBOARD_DESIGN_SPEC.md)
- [ ] Create Figma file structure
- [ ] Design health score hero component (3 states: good/warning/critical)

**Product Manager:**

- [ ] Draft user testing script (see Testing Script section below)
- [ ] Create screener survey for participant recruitment
- [ ] Post recruitment ads (relevant SMB forums, LinkedIn groups)

**CTO/Tech Lead:**

- [ ] Review consulting report with engineering team
- [ ] Assess technical feasibility of recommendations
- [ ] Identify architectural dependencies

#### Tuesday (Day 2)

**Product Designer:**

- [ ] Design proactive coach card components
- [ ] Design goals + tasks unified view
- [ ] Design metrics snapshot cards

**Product Manager:**

- [ ] Screen and schedule 10 participants
- [ ] Mix: 3 restaurants, 3 retail, 2 services, 2 contractors
- [ ] Confirm incentives ($100 Amazon gift card per participant)

**Engineering Team:**

- [ ] Estimate Phase 1 implementation (see detailed breakdown below)
- [ ] Identify technical risks and dependencies

#### Wednesday (Day 3)

**Product Designer:**

- [ ] Complete all desktop designs
- [ ] Create mobile responsive variants
- [ ] Add interaction annotations (hover states, animations)

**Product Manager:**

- [ ] Finalize testing script
- [ ] Prepare testing environment (Zoom, recording setup)
- [ ] Create analysis spreadsheet for tracking responses

**Data Analyst:**

- [ ] Pull current baseline metrics:
  - DAU/MAU ratio
  - Average session time
  - Health score view rate
  - Task completion rate
  - Churn rate by cohort

#### Thursday (Day 4)

**Product Designer:**

- [ ] Create clickable Figma prototype
- [ ] Add realistic data (use anonymized customer data)
- [ ] Test prototype flow internally

**Product Manager:**

- [ ] Dry run testing session with internal stakeholder
- [ ] Refine questions based on feedback
- [ ] Send confirmation emails to participants

**Engineering:**

- [ ] Create technical spec for Phase 1 (see Engineering Tasks below)
- [ ] Set up development environment for V6 branch

#### Friday (Day 5)

**Product Designer:**

- [ ] Final prototype polish
- [ ] Create alternate version (current chat UI) for comparison
- [ ] Document design decisions for handoff

**Product Manager:**

- [ ] Conduct first 2 user testing sessions
- [ ] Record and take detailed notes
- [ ] Initial observations log

---

### Week 2: Test & Analyze

#### Monday-Wednesday (Days 6-10)

**Product Manager:**

- [ ] Conduct remaining 8 user testing sessions (2-3 per day)
- [ ] Document insights after each session
- [ ] Identify emerging patterns

**Product Designer:**

- [ ] Observe testing sessions (attend at least 5)
- [ ] Note UI/UX issues in real-time
- [ ] Create quick fixes for major issues

**Engineering:**

- [ ] Begin Phase 1 technical architecture
- [ ] Set up component library structure
- [ ] Create API endpoint specifications

#### Thursday (Day 11)

**Product Manager:**

- [ ] Synthesize all testing feedback
- [ ] Create findings presentation
- [ ] Quantify key metrics:
  - % who understood health score concept
  - % who preferred fitness dashboard vs. chat
  - Average time to identify top priority
  - % willing to pay premium pricing

**Product Designer:**

- [ ] Update designs based on testing insights
- [ ] Create v2 prototype with improvements
- [ ] Document design system decisions

#### Friday (Day 12) - GO/NO-GO DECISION

**Leadership Team Meeting:**

- [ ] Present testing results
- [ ] Show updated designs
- [ ] Review engineering estimates
- [ ] **DECIDE:** Proceed to Phase 1 or pivot?

**If GO:**

- [ ] Kickoff Phase 1 sprint planning
- [ ] Assign engineering resources
- [ ] Set success metrics and milestones

**If NO-GO:**

- [ ] Document learnings
- [ ] Plan incremental improvements to current UI
- [ ] Consider alternative approaches

---

## Phase 1: Foundation (Weeks 3-6) - IF VALIDATED

### Goal

Implement persistent health metrics without disrupting current functionality.

### Engineering Tasks

#### Frontend (apps/smb/src/)

**Task 1.1: Create Health Score Header Component (3 days)**

```typescript
// File: apps/smb/src/components/HealthScoreHeader.tsx

interface HealthScoreHeaderProps {
  score: number;
  previousScore: number;
  criticalAlerts: Alert[];
  positiveSignals: Signal[];
  onViewReport: () => void;
  onAskCoach: () => void;
}

// Component features:
// - Sticky positioning on scroll
// - Animated score counter
// - Expandable details panel
// - Gradient background based on score
```

**Acceptance Criteria:**

- [ ] Score animates on change (0.5s count-up)
- [ ] Trend arrow shows correctly (up/down/stable)
- [ ] Max 2 alerts + 2 signals visible
- [ ] Responsive on mobile (80px height)
- [ ] Accessible (WCAG AA compliant)

**Task 1.2: Create Proactive Coach Card Component (4 days)**

```typescript
// File: apps/smb/src/components/ProactiveCoachCard.tsx

interface CoachRecommendation {
  id: string;
  priority: 'critical' | 'important' | 'suggestion';
  title: string;
  description: string;
  actions: Array<{
    label: string;
    onClick: () => void;
    variant: 'primary' | 'secondary';
  }>;
  dismissible: boolean;
  createdAt: Date;
}

// Component features:
// - Priority-based styling (red/yellow/blue)
// - Slide-in animation on appear
// - Slide-out animation on dismiss
// - Action button handlers
```

**Acceptance Criteria:**

- [ ] Cards stack vertically (max 3 visible)
- [ ] Dismiss persists to backend
- [ ] Actions trigger correct flows
- [ ] Mobile: Horizontal carousel (swipeable)
- [ ] Loading state (skeleton)

**Task 1.3: Refactor Layout Structure (5 days)**

```typescript
// File: apps/smb/src/pages/CoachV6.tsx

// New layout hierarchy:
// <HealthScoreHeader /> (sticky)
// <ProactiveCoachCards />
// <ContentGrid>
//   <GoalsColumn />
//   <TasksColumn />
//   <MetricsColumn />
// </ContentGrid>
// <ChatInterface collapsed />
```

**Acceptance Criteria:**

- [ ] Health score always visible (sticky)
- [ ] Three-column grid on desktop
- [ ] Stacked on tablet
- [ ] Tabbed on mobile
- [ ] Smooth transitions between layouts
- [ ] No layout shift on data load

**Task 1.4: Migrate State Management (3 days)**

```typescript
// File: apps/smb/src/stores/coachStore.ts

interface CoachStore {
  healthScore: HealthScore;
  recommendations: CoachRecommendation[];
  dismissedRecommendations: string[];
  fetchHealthScore: () => Promise<void>;
  fetchRecommendations: () => Promise<void>;
  dismissRecommendation: (id: string) => Promise<void>;
}

// Use Zustand for global state
// TanStack Query for server state
```

**Acceptance Criteria:**

- [ ] Health score updates without page refresh
- [ ] Recommendations poll every 5 minutes
- [ ] Dismissed items persist across sessions
- [ ] Optimistic UI updates
- [ ] Error states handled gracefully

---

#### Backend (services/kernel/)

**Task 1.5: Health Score Trend API (3 days)**

```python
# File: services/kernel/routes/health.py

@router.get("/v1/tenants/{tenant_id}/health-score/trend")
async def get_health_score_trend(
    tenant_id: str,
    period: Literal["7d", "30d", "90d"] = "30d"
) -> HealthScoreTrend:
    """
    Returns health score history with component breakdown.
    
    Components:
    - Cash flow health (40% weight)
    - Revenue growth (25% weight)
    - Profitability (20% weight)
    - Operational efficiency (15% weight)
    """
    pass
```

**Acceptance Criteria:**

- [ ] Returns last 30 data points by default
- [ ] Component scores included
- [ ] Performance < 500ms for 90d query
- [ ] Cached for 1 hour
- [ ] Historical data backfilled for existing tenants

**Task 1.6: Daily Insights Generation Job (4 days)**

```python
# File: services/kernel/jobs/daily_insights.py

async def generate_daily_insights(tenant_id: str):
    """
    Runs at 6am local time for each tenant.
    
    Steps:
    1. Fetch yesterday's data (revenue, expenses, inventory)
    2. Compare to historical baseline (last 7/30/90 days)
    3. Identify anomalies (>20% deviation)
    4. Calculate health score components
    5. Generate recommendations using coach agent
    6. Store in insights table
    7. Trigger push notification if critical
    """
    pass
```

**Acceptance Criteria:**

- [ ] Runs reliably via Celery/Temporal
- [ ] Handles timezone correctly per tenant
- [ ] Generates 1-3 recommendations per tenant
- [ ] Stores in PostgreSQL insights table
- [ ] Fallback if external data unavailable
- [ ] Monitoring and alerting on failures

**Task 1.7: Coach Recommendations API (3 days)**

```python
# File: services/kernel/routes/coach_recommendations.py

@router.get("/v1/tenants/{tenant_id}/coach/recommendations")
async def get_recommendations(
    tenant_id: str,
    active_only: bool = True,
    limit: int = 10
) -> List[CoachRecommendation]:
    """
    Returns prioritized list of coach recommendations.
    
    Priority order:
    1. Critical (cash flow risk, compliance deadline)
    2. Important (goal blockers, significant trends)
    3. Suggestions (optimizations, best practices)
    """
    pass

@router.post("/v1/tenants/{tenant_id}/coach/recommendations/{rec_id}/dismiss")
async def dismiss_recommendation(
    tenant_id: str,
    rec_id: str
) -> SuccessResponse:
    """Mark recommendation as dismissed."""
    pass
```

**Acceptance Criteria:**

- [ ] Returns max 10 recommendations
- [ ] Sorted by priority then recency
- [ ] Dismissed items filtered out
- [ ] Performance < 200ms
- [ ] WebSocket support for real-time updates

---

#### AI/Agent (packages/agent/)

**Task 1.8: Coach Recommendation Templates (4 days)**

```python
# File: packages/agent/coach_templates.py

class CoachRecommendationEngine:
    """Generates contextual business recommendations."""
    
    templates = {
        "cash_flow_risk": {
            "trigger": lambda ctx: ctx.cash < ctx.payables_7d,
            "priority": "critical",
            "template": """
            {business_name}, you have ${payables} due in {days} days 
            but only ${cash} available. I recommend:
            
            1. {action_primary}
            2. {action_secondary}
            3. {action_tertiary}
            """,
            "actions": [
                {"type": "contact_vendor", "entity": "top_payable"},
                {"type": "follow_up_invoices", "filter": "overdue"},
                {"type": "review_loc", "amount": "shortfall"}
            ]
        },
        # ... 20+ other templates
    }
    
    async def generate_recommendations(
        self, 
        tenant_id: str
    ) -> List[CoachRecommendation]:
        """
        1. Fetch tenant context (financial data, goals, tasks)
        2. Evaluate all template triggers
        3. Rank by priority and relevance
        4. Generate personalized text using LLM
        5. Return top 3 recommendations
        """
        pass
```

**Acceptance Criteria:**

- [ ] 20+ recommendation templates implemented
- [ ] Personalized to business type (restaurant vs. retail)
- [ ] Uses GPT-4 for natural language generation
- [ ] Fallback templates if LLM fails
- [ ] Unit tests for trigger logic
- [ ] Integration tests with real tenant data

**Task 1.9: Business Type Classification (3 days)**

```python
# File: packages/agent/business_classifier.py

class BusinessClassifier:
    """Classify business type from tenant data."""
    
    async def classify(self, tenant_id: str) -> BusinessType:
        """
        Analyze:
        - Industry from tenant profile
        - Transaction patterns (frequency, amounts)
        - Inventory characteristics
        - Customer patterns (B2C vs B2B)
        
        Returns: BusinessType enum
        """
        pass
```

**Acceptance Criteria:**

- [ ] Classifies into 8 categories (retail, restaurant, services, etc.)
- [ ] 85%+ accuracy on test set
- [ ] Falls back to manual classification if uncertain
- [ ] Runs on tenant onboarding + monthly refresh
- [ ] Stored in tenant metadata

---

### Testing & QA (Week 6)

**Task 1.10: Integration Testing (3 days)**

- [ ] Health score updates correctly on data changes
- [ ] Recommendations appear within 10s of generation
- [ ] Dismiss persists across page refresh
- [ ] Mobile responsive layouts work on iOS/Android
- [ ] Accessibility audit (lighthouse score 90+)

**Task 1.11: Performance Testing (2 days)**

- [ ] Page load < 1s on 3G connection
- [ ] Health score fetch < 500ms
- [ ] Recommendations API < 200ms
- [ ] No memory leaks on long sessions
- [ ] Bundle size < 200kb gzipped

**Task 1.12: User Acceptance Testing (2 days)**

- [ ] Deploy to staging with 10 beta users
- [ ] Collect feedback via Hotjar surveys
- [ ] Monitor usage analytics
- [ ] Fix critical bugs
- [ ] Document known issues for Phase 2

---

### Success Metrics (End of Phase 1)

**Engagement:**

- Health score views: 30% → **60%** of users daily
- Average session time: 3.2 min → **5 min**
- Return visits: 2.5/week → **3.5/week**

**Feature Adoption:**

- % users who view health score: **80%+**
- % users who act on recommendation: **25%+**
- % users who dismiss (not ignore): **15%+**

**Performance:**

- Page load time: **< 1s** (90th percentile)
- Time to interactive: **< 1.5s**
- Error rate: **< 0.5%**

**If metrics hit targets: Proceed to Phase 2**
**If metrics miss: Iterate for 2 more weeks before Phase 2**

---

## Phase 2: Proactive Coach (Weeks 7-9)

### Goal

Enable AI to initiate conversations and send real-time alerts.

### Major Features

**2.1 WebSocket Real-Time Updates**

- Push new recommendations without refresh
- Live health score updates
- Real-time task completion notifications

**2.2 Smart Notification System**

- In-app notifications (slide-in cards)
- Email digest (daily/weekly)
- SMS for critical alerts (opt-in)
- Push notifications (mobile app)

**2.3 Recommendation Action Flows**

- "Create Action Plan" → Multi-step wizard
- "Show Details" → Drill-down modal with data viz
- "Tell Me More" → Opens contextual chat

**2.4 Feedback Loop**

- "Was this helpful?" on every recommendation
- Track dismissal reasons (not relevant, wrong data, etc.)
- Use feedback to improve recommendation quality

---

## Phase 3: Personalization (Weeks 10-12)

### Goal

Adapt interface based on business type and user behavior.

### Major Features

**3.1 Industry-Specific Dashboards**

- Restaurant: Food cost %, labor %, daily covers
- Retail: Inventory turnover, foot traffic, basket size
- Services: Utilization rate, billable hours, project pipeline
- Contractor: Job completion rate, material costs, crew efficiency

**3.2 Contextual Prompts**

- Morning (8am): "Good morning! Here's your daily briefing"
- Lunch (12pm): "How's today's performance vs. yesterday?"
- EOD (5pm): "Today's summary: 3/5 tasks complete"
- Custom: Based on business hours from tenant profile

**3.3 Role-Based Views**

- Owner: Full health score + strategic insights
- Manager: Operational metrics + task assignment
- Staff: Task list only

**3.4 Benchmarking**

- "Your inventory turnover is better than 73% of similar retailers"
- "Top performers in your category achieve 85% gross margin"
- Anonymized peer comparison

---

## Resource Requirements

### Team Composition

**Phase 1 (Weeks 3-6):**

- 2 Senior Frontend Engineers (React, TypeScript)
- 1 Senior Backend Engineer (Python, FastAPI)
- 1 AI/ML Engineer (LLM integration, prompt engineering)
- 1 Product Designer (Figma, design systems)
- 1 QA Engineer (automated testing)
- 1 Product Manager (coordination, user feedback)

**Phase 2 (Weeks 7-9):**

- Same team + 1 DevOps Engineer (WebSocket infrastructure)

**Phase 3 (Weeks 10-12):**

- Same team + 1 Data Analyst (benchmarking data)

### Budget Breakdown

| Phase | Duration | Team Size | Cost |
|-------|----------|-----------|------|
| Validation | 2 weeks | 2 people | $7,500 |
| Phase 1 | 4 weeks | 6 people | $80,000 |
| Phase 2 | 3 weeks | 7 people | $60,000 |
| Phase 3 | 3 weeks | 8 people | $70,000 |
| **Total** | **12 weeks** | **6-8 avg** | **$217,500** |

*Assumes $150/hr blended rate*

---

## Risk Mitigation

### Risk 1: Validation Fails

**Mitigation:** Validation sprint is only $7.5k. If users don't prefer fitness dashboard, pivot to incremental improvements.

### Risk 2: Backend Performance Issues

**Mitigation:** Load testing in Phase 1 week 5. If issues found, add caching layer before Phase 2.

### Risk 3: AI Recommendations Are Wrong

**Mitigation:** Human review of first 100 recommendations. Confidence threshold: Only show if 80%+ confident.

### Risk 4: User Resistance to Change

**Mitigation:** Offer "Classic View" toggle for 3 months. Gradual rollout (10% → 50% → 100%).

### Risk 5: Scope Creep

**Mitigation:** Strict feature freeze per phase. "Phase 4" backlog for good ideas.

---

## Go-to-Market Plan

### Pre-Launch (Week 11)

**Marketing:**

- [ ] Create landing page for "Business Fitness Coach"
- [ ] Record product demo video (3 minutes)
- [ ] Write 3 blog posts (SEO: "business health score", "AI business coach")
- [ ] Design comparison chart (Dyocense vs. competitors)

**Sales:**

- [ ] Update pitch deck with new positioning
- [ ] Create ROI calculator (show value of proactive insights)
- [ ] Train sales team on new features
- [ ] Identify 20 high-value prospects for early access

**Customer Success:**

- [ ] Create onboarding checklist for new users
- [ ] Record tutorial videos (5 × 2-min clips)
- [ ] Update help docs
- [ ] Prepare migration guide for existing users

### Launch (Week 12)

**Day 1: Soft Launch**

- [ ] Enable for 10 beta users
- [ ] Monitor closely for bugs
- [ ] Hotfix deployment ready

**Day 3: 50% Rollout**

- [ ] Enable for 50% of users (randomly assigned)
- [ ] A/B test: V5 vs V6 engagement
- [ ] Collect feedback via in-app survey

**Day 7: Full Rollout**

- [ ] Enable for all users
- [ ] Send announcement email
- [ ] Press release (if metrics strong)
- [ ] LinkedIn/Twitter promotion

**Day 14: Retrospective**

- [ ] Review metrics vs. targets
- [ ] Collect team feedback
- [ ] Plan Phase 4 (advanced features)

---

## Success Criteria Summary

### Must-Have (Launch Blockers)

- [ ] Health score visible and accurate for 100% of users
- [ ] At least 1 relevant recommendation per user per week
- [ ] No critical bugs (P0/P1)
- [ ] Page load time < 1s (90th percentile)
- [ ] Mobile responsive on iOS/Android

### Should-Have (Post-Launch Fix)

- [ ] 60%+ of users view health score daily
- [ ] 25%+ of users act on recommendations
- [ ] 5+ min average session time
- [ ] < 0.5% error rate

### Nice-to-Have (Phase 4)

- [ ] Benchmarking data
- [ ] Multi-user collaboration
- [ ] Custom metrics
- [ ] API access for power users

---

## Appendix A: User Testing Script

### Introduction (2 minutes)

"Thank you for participating! We're designing a new interface for business owners like you. There are no wrong answers - we want honest feedback. I'll show you a prototype and ask questions. Please think aloud as you explore."

### Task 1: First Impression (3 minutes)

"This is the home screen you'd see when opening the app. Take 30 seconds to look around, then tell me: What is this app trying to help you do?"

**Look for:**

- Do they mention "health" or "fitness"?
- Do they understand the score?
- Do they notice the recommendations?

### Task 2: Find Priority (2 minutes)

"Imagine you're checking this quickly during a busy morning. What's the most important thing you should focus on today?"

**Look for:**

- Time to identify (target: <10 seconds)
- Do they find the critical alert?
- Confidence in their answer

### Task 3: Take Action (3 minutes)

"Let's say you want to address the cash flow issue. Show me how you'd do that."

**Look for:**

- Can they find the action button?
- Do they understand the suggested steps?
- Would they actually do this in real life?

### Task 4: Compare to Current (5 minutes)

*Show current chat interface*
"Now let me show you the current version. Which do you prefer and why?"

**Look for:**

- Clear preference or "it depends"
- Reasoning (speed, clarity, trust, etc.)
- What they'd want from each version

### Task 5: Pricing (2 minutes)

"The current version is $75/month. If the new version helps you make faster, better decisions, what would you be willing to pay?"

**Look for:**

- Price sensitivity
- Perceived value
- Premium willingness (target: $150-250/mo)

### Closing (3 minutes)

"What questions do you have? Any final thoughts?"

**Total: 20 minutes**

---

## Appendix B: Technical Dependencies

### Required Infrastructure

- [ ] PostgreSQL: insights table, recommendations table
- [ ] Redis: Caching health scores and recommendations
- [ ] Celery/Temporal: Job scheduler for daily insights
- [ ] WebSocket: Real-time updates (Phase 2)
- [ ] CDN: Asset delivery for performance

### Third-Party Services

- [ ] OpenAI API: GPT-4 for recommendation generation
- [ ] Stripe: Updated billing for new pricing tiers
- [ ] Sentry: Error tracking and monitoring
- [ ] Hotjar: User behavior analytics
- [ ] Mixpanel: Product analytics

### Development Tools

- [ ] Figma: Design collaboration
- [ ] Storybook: Component library documentation
- [ ] Playwright: E2E testing
- [ ] k6: Load testing
- [ ] GitHub Actions: CI/CD pipeline

---

## Appendix C: Rollback Plan

If critical issues arise post-launch:

**Scenario 1: Data Accuracy Issues**

- [ ] Disable health score display
- [ ] Show static message: "Calculating your health score..."
- [ ] Fix calculation logic
- [ ] Re-enable after validation

**Scenario 2: Performance Degradation**

- [ ] Enable aggressive caching (5-min stale data acceptable)
- [ ] Disable real-time updates temporarily
- [ ] Scale backend horizontally
- [ ] Optimize slow queries

**Scenario 3: User Confusion**

- [ ] Add prominent "?" help icons
- [ ] Show tutorial modal on first visit
- [ ] Offer "Classic View" toggle prominently
- [ ] Schedule webinar to explain changes

**Scenario 4: Complete Rollback**

- [ ] Feature flag to disable V6 entirely
- [ ] Revert to V5 for all users
- [ ] Preserve V6 data for future migration
- [ ] Communicate transparently to users

---

**Document Owner:** Product Team  
**Last Updated:** November 13, 2025  
**Next Review:** After validation sprint completion (Week 2)
