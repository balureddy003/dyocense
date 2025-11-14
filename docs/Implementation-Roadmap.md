# 🗓️ Dyocense Implementation Roadmap

**Version:** 4.0 (Cost-Optimized Monolith)  
**Duration:** 12 Weeks  
**Target:** Production-Ready MVP for 50 SMBs  
**Last Updated:** November 14, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Phase 0: Foundation & Simplification](#phase-0-foundation--simplification-weeks-1-4)
3. [Phase 1: Core Intelligence](#phase-1-core-intelligence-weeks-5-8)
4. [Phase 2: Polish & Launch](#phase-2-polish--launch-weeks-9-12)
5. [Success Criteria](#success-criteria)
6. [Risk Mitigation](#risk-mitigation)

---

## 🎯 Overview

### **Project Goals**

Transform Dyocense from a complex microservices architecture to a **cost-effective monolith** that delivers:

- **Business AI Coaching** (not just dashboards)
- **Mathematical Optimization** (inventory, staffing, pricing)
- **Forecasting with Uncertainty** (ARIMA, Prophet, ensemble methods)
- **Causal Inference** (explain why metrics changed)
- **<$30/month pricing** for SMBs (vs. $500-1500 traditional BI)

### **Architecture Transformation**

| Metric | Before (v3.0) | After (v4.0) | Impact |
|--------|--------------|--------------|--------|
| Services | 19 microservices | 1 monolith | 80% ops reduction |
| Databases | 4 (PostgreSQL, Vector DB, Graph DB, Redis) | 1 (PostgreSQL) | $700/mo savings |
| LLM Costs | 100% cloud ($5/100 queries) | 70% local, 30% cloud | 80% cost reduction |
| Deployment Time | ~2 hours (K8s) | <5 minutes (Docker) | 96% faster |
| Infrastructure Cost | $5/tenant/mo | <$1/tenant/mo | 80% savings |

### **Delivery Timeline**

```
Week 1-4: Foundation (PostgreSQL, Monolith, RLS, Observability)
Week 5-8: Intelligence (Optimization, Forecasting, Causal AI)
Week 9-12: Launch (Polish, Performance, Security, Beta)
```

---

## 🏗️ Phase 0: Foundation & Simplification (Weeks 1-4)

### **Week 1: Monolith Structure + PostgreSQL Migration**

#### **Objectives**

- Create unified backend structure
- Migrate all data to PostgreSQL with extensions
- Set up local development environment

#### **Tasks**

**Day 1-2: Monolith Setup**

- [ ] Create `backend/` directory structure:

  ```
  backend/
  ├── main.py              # FastAPI app entry point
  ├── config.py            # Environment config
  ├── dependencies.py      # Dependency injection
  ├── models/              # SQLAlchemy models
  ├── routes/              # API endpoints
  ├── services/            # Business logic
  │   ├── coach/          # AI coach service
  │   ├── optimizer/      # Optimization engine
  │   ├── forecaster/     # Forecasting service
  │   ├── evidence/       # Causal inference
  │   └── connectors/     # Data ingestion
  ├── agents/              # LangGraph agents
  ├── schemas/             # Pydantic schemas
  └── utils/               # Helpers
  ```

- [ ] Consolidate 19 microservice configs into single `config.py`
- [ ] Set up Docker Compose with PostgreSQL 16+ (+ extensions)

**Day 3-4: PostgreSQL Extensions**

- [ ] Install TimescaleDB for time-series metrics
- [ ] Install pgvector for semantic search (embeddings)
- [ ] Install Apache AGE for graph queries (evidence)
- [ ] Install pg_cron for scheduled jobs
- [ ] Migrate existing data from separate databases

**Day 5: Local Development**

- [ ] Write `Makefile` with common commands:
  - `make dev` (start all services)
  - `make test` (run tests)
  - `make migrate` (apply DB migrations)
- [ ] Update `README.md` with quick start guide
- [ ] Test end-to-end local setup

#### **Deliverables**

- ✅ Single FastAPI monolith (replaces 19 services)
- ✅ PostgreSQL with 4 extensions (replaces 4 databases)
- ✅ Docker Compose for local dev
- ✅ Updated developer documentation

#### **Success Metrics**

- PostgreSQL handles 10,000 requests/sec (load test)
- Local dev setup completes in <10 minutes
- All existing data migrated without loss

---

### **Week 2: Core Data Models + Row-Level Security**

#### **Objectives**

- Define PostgreSQL schema for multi-tenancy
- Implement Row-Level Security (RLS) for tenant isolation
- Migrate key entities (tenants, users, goals, metrics)

#### **Tasks**

**Day 1-2: Schema Design**

- [ ] Create SQLAlchemy models for:
  - `tenants` (companies using Dyocense)
  - `users` (SMB employees)
  - `smart_goals` (goal lifecycle tracking)
  - `business_metrics` (TimescaleDB hypertable)
  - `coaching_sessions` (conversation history + embeddings)
  - `data_sources` (connector configurations)
  - `evidence_graph` (causal relationships)
  - `external_benchmarks` (industry data)
- [ ] Write Alembic migrations for schema creation

**Day 3-4: Row-Level Security (RLS)**

- [ ] Enable RLS on all tenant-scoped tables
- [ ] Create PostgreSQL policies:

  ```sql
  CREATE POLICY tenant_isolation ON business_metrics
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
  ```

- [ ] Implement middleware to set `app.current_tenant` per request
- [ ] Write tests to verify tenant data isolation

**Day 5: Data Migration**

- [ ] Migrate existing tenant data from microservices DBs
- [ ] Validate data integrity (checksums, row counts)
- [ ] Backfill missing fields (if any)

#### **Deliverables**

- ✅ Complete PostgreSQL schema (10+ tables)
- ✅ RLS policies for all tenant-scoped data
- ✅ Alembic migrations (version-controlled schema)
- ✅ 100% data migrated from old DBs

#### **Success Metrics**

- RLS prevents cross-tenant data leakage (security audit)
- Query performance <100ms (p95) for common operations
- Zero data loss during migration

---

### **Week 3: AI Coach Integration + Hybrid LLM Routing**

#### **Objectives**

- Consolidate multi-agent coach into monolith
- Implement hybrid LLM routing (70% local, 30% cloud)
- Optimize response latency (<3 seconds)

#### **Tasks**

**Day 1-2: LangGraph Agent Setup**

- [ ] Create `backend/agents/` module with LangGraph state machines
- [ ] Define agent nodes:
  - `goal_planner` (decompose user goals into SMART goals)
  - `evidence_analyzer` (causal root cause analysis)
  - `forecaster` (predict future metrics)
  - `optimizer` (recommend optimal actions)
- [ ] Implement streaming responses (SSE for real-time output)

**Day 3-4: Hybrid LLM Routing**

- [ ] Deploy local Llama 3 8B (Ollama or vLLM)
- [ ] Implement routing logic:

  ```python
  if query_complexity < threshold:
      response = local_llm(query)  # 70% of queries
  else:
      response = openai_gpt4o(query)  # 30% of queries
  ```

- [ ] Add LLM observability (track costs, latency, token usage)
- [ ] Implement caching for repeated queries (Redis)

**Day 5: Testing & Optimization**

- [ ] Load test: 100 concurrent users asking coach questions
- [ ] Optimize prompt templates for local LLM accuracy
- [ ] Add fallback logic (if local LLM fails, use cloud)

#### **Deliverables**

- ✅ Unified AI coach in monolith (no separate service)
- ✅ Hybrid LLM routing (80% cost savings)
- ✅ Streaming responses (<3s latency)
- ✅ LLM cost tracking dashboard (Grafana)

#### **Success Metrics**

- Coach response time <3 seconds (p95)
- Local LLM handles 70% of queries (cost tracking)
- User satisfaction score >4/5 (beta feedback)

---

### **Week 4: Observability + Docker Deployment**

#### **Objectives**

- Set up Prometheus + Grafana for metrics
- Implement structured logging (Loki)
- Deploy to staging environment (Docker Compose)

#### **Tasks**

**Day 1-2: Metrics & Tracing**

- [ ] Instrument FastAPI with Prometheus metrics:
  - Request rate, latency (p50, p95, p99)
  - Database query time
  - LLM API calls (cost, latency)
- [ ] Add OpenTelemetry tracing (Jaeger)
- [ ] Create Grafana dashboards:
  - System health (CPU, memory, disk)
  - Business metrics (goals created, coach queries)
  - Cost metrics (LLM spend, infrastructure)

**Day 3-4: Logging**

- [ ] Implement structured logging (JSON format)
- [ ] Set up Loki for log aggregation
- [ ] Add log correlation (trace IDs in logs)
- [ ] Configure log retention (30 days)

**Day 5: Staging Deployment**

- [ ] Write `docker-compose.production.yml` (optimized for staging/prod)
- [ ] Deploy to cloud VM (DigitalOcean, Hetzner, or Linode)
- [ ] Set up CI/CD pipeline (GitHub Actions):
  - Lint → Test → Build → Deploy
- [ ] Smoke test all endpoints in staging

#### **Deliverables**

- ✅ Prometheus + Grafana observability stack
- ✅ Structured logging with Loki
- ✅ Staging environment deployed (Docker Compose)
- ✅ CI/CD pipeline automated

#### **Success Metrics**

- All critical metrics visible in Grafana
- Logs searchable within 5 seconds (Loki)
- Staging deployment takes <5 minutes (CI/CD)

---

## 🧠 Phase 1: Core Intelligence (Weeks 5-8)

### **Week 5: Optimization Engine (Inventory, Staffing, Pricing)**

#### **Objectives**

- Build mathematical optimization module
- Implement 3 SMB use cases (inventory, staffing, budget)
- Integrate with AI coach for recommendations

#### **Tasks**

**Day 1-2: Linear Programming Framework**

- [ ] Set up OR-Tools and PuLP in `backend/services/optimizer/`
- [ ] Create abstract `OptimizationModel` base class
- [ ] Implement constraint validation logic

**Day 3-4: Use Case Models**

- [ ] **Inventory Optimization:**
  - Minimize holding costs + stockout penalties
  - Constraints: storage capacity, demand forecast, supplier lead times
- [ ] **Staffing Optimization:**
  - Minimize labor cost while meeting service levels
  - Constraints: labor laws, skill requirements, shift preferences
- [ ] **Budget Allocation:**
  - Maximize ROI across marketing channels
  - Constraints: total budget, channel capacity, diminishing returns

**Day 5: Integration & Testing**

- [ ] Expose optimization API endpoints (`/optimize/inventory`, etc.)
- [ ] Integrate with coach agent (coach suggests optimization runs)
- [ ] Test with real SMB data (anonymized restaurant data)

#### **Deliverables**

- ✅ Optimization engine (3 models: inventory, staffing, budget)
- ✅ API endpoints for optimization requests
- ✅ Integration with AI coach

#### **Success Metrics**

- Optimization solves <5 seconds for typical SMB scale
- Models pass validation tests (known optimal solutions)
- Coach successfully triggers optimization on user request

---

### **Week 6: Forecasting Engine (ARIMA, Prophet, Ensemble)**

#### **Objectives**

- Build time-series forecasting module
- Implement uncertainty quantification (confidence intervals)
- Support multiple forecast horizons (daily, weekly, monthly)

#### **Tasks**

**Day 1-2: Forecasting Framework**

- [ ] Set up `backend/services/forecaster/` module
- [ ] Install libraries: statsmodels (ARIMA), Prophet, XGBoost
- [ ] Create `ForecastModel` base class with fit/predict interface

**Day 3-4: Model Implementations**

- [ ] **Auto-ARIMA:** Automatic parameter selection
- [ ] **Prophet:** Handle seasonality, holidays, trend changes
- [ ] **XGBoost:** Feature-based forecasting (lagged variables, exogenous features)
- [ ] **Ensemble:** Weighted average of all models (improves accuracy)

**Day 5: API & Integration**

- [ ] Expose `/forecast` endpoint (accept metric, horizon, confidence level)
- [ ] Store forecasts in TimescaleDB (`forecasts` table)
- [ ] Integrate with coach (coach shows forecasts in conversations)

#### **Deliverables**

- ✅ Forecasting engine (4 models: ARIMA, Prophet, XGBoost, Ensemble)
- ✅ Uncertainty quantification (95% confidence intervals)
- ✅ API for forecast requests

#### **Success Metrics**

- Forecast accuracy (MAPE) <15% on test data
- Forecasts generated <10 seconds
- Coach displays forecasts in natural language

---

### **Week 7: Evidence Engine (Causal Inference)**

#### **Objectives**

- Build causal inference module
- Implement root cause analysis for metric changes
- Generate counterfactual scenarios ("what if we had...")

#### **Tasks**

**Day 1-2: Causal Graph Construction**

- [ ] Set up `backend/services/evidence/` module
- [ ] Install DoWhy, pgmpy, CausalNex
- [ ] Implement Bayesian network learning (structure + parameters)
- [ ] Store causal graphs in PostgreSQL (Apache AGE or JSONB)

**Day 3-4: Causal Analysis Methods**

- [ ] **Granger Causality:** Detect time-lagged causal relationships
- [ ] **Propensity Score Matching:** Estimate causal effects from observational data
- [ ] **Counterfactual Reasoning:** "If we had increased marketing spend by 20%, revenue would have..."

**Day 5: Integration**

- [ ] Expose `/evidence/explain` endpoint (explain why metric changed)
- [ ] Integrate with coach (coach cites evidence in explanations)
- [ ] Visualize causal graphs in frontend (D3.js or Cytoscape.js)

#### **Deliverables**

- ✅ Evidence engine (causal inference module)
- ✅ API for "explain why" queries
- ✅ Causal graph visualization

#### **Success Metrics**

- Causal graphs accurately identify known relationships (validation tests)
- Explanations pass human review (domain expert evaluation)
- Coach uses evidence in >50% of explanations

---

### **Week 8: External Benchmarks (FRED, IBISWorld, Industry Data)**

#### **Objectives**

- Integrate external data sources for benchmarking
- Enrich SMB context with industry/economic data
- Enable comparative insights ("your revenue growth vs. industry average")

#### **Tasks**

**Day 1-2: API Integrations**

- [ ] Implement FRED API client (Federal Reserve Economic Data)
- [ ] Implement IBISWorld API client (or scraper if no API)
- [ ] Implement Census Bureau API (optional: demographic data)

**Day 3-4: Data Ingestion**

- [ ] Create `external_benchmarks` table in PostgreSQL
- [ ] Write ETL pipelines (Airflow DAGs or pg_cron jobs)
- [ ] Schedule daily/weekly data refreshes

**Day 5: Coach Integration**

- [ ] Add benchmark retrieval to coach context (RAG)
- [ ] Implement comparison logic ("Your sales growth is 15% vs. industry average of 8%")
- [ ] Test with real SMB data

#### **Deliverables**

- ✅ External data integrations (3+ sources)
- ✅ Automated data refresh pipelines
- ✅ Coach uses benchmarks in recommendations

#### **Success Metrics**

- Benchmark data refreshes daily (automated)
- Coach cites external data in >30% of responses
- Benchmarks improve recommendation quality (user feedback)

---

## 🚀 Phase 2: Polish & Launch (Weeks 9-12)

### **Week 9: Frontend Polish + Responsive Design**

#### **Objectives**

- Improve SMB portal UI/UX
- Ensure mobile responsiveness
- Add interactive visualizations

#### **Tasks**

**Day 1-2: Component Library**

- [ ] Audit existing UI components (`apps/smb/`)
- [ ] Standardize design system (colors, typography, spacing)
- [ ] Refactor components for reusability (Storybook)

**Day 3-4: Dashboards & Visualizations**

- [ ] Redesign main dashboard (goal progress, metrics, insights)
- [ ] Add interactive charts (Chart.js or Recharts)
- [ ] Implement drill-down views (click metric → see details)

**Day 5: Mobile Optimization**

- [ ] Test on mobile devices (iOS, Android)
- [ ] Fix layout issues (responsive breakpoints)
- [ ] Optimize touch interactions (button sizes, gestures)

#### **Deliverables**

- ✅ Polished UI with consistent design system
- ✅ Interactive dashboards
- ✅ Mobile-responsive layout

#### **Success Metrics**

- Lighthouse score >90 (performance, accessibility)
- Mobile usability passes Google test
- User testing shows >4/5 satisfaction

---

### **Week 10: Performance Optimization**

#### **Objectives**

- Optimize database queries (<100ms p95)
- Implement caching (Redis)
- Reduce frontend bundle size

#### **Tasks**

**Day 1-2: Database Optimization**

- [ ] Run `EXPLAIN ANALYZE` on slow queries
- [ ] Add missing indexes (TimescaleDB compression)
- [ ] Optimize N+1 queries (eager loading)

**Day 3-4: Caching Strategy**

- [ ] Cache LLM responses (Redis)
- [ ] Cache frequently accessed data (metrics, benchmarks)
- [ ] Implement cache invalidation logic

**Day 5: Frontend Performance**

- [ ] Code-split React bundles (lazy loading)
- [ ] Optimize images (WebP format, lazy loading)
- [ ] Enable CDN caching (CloudFlare)

#### **Deliverables**

- ✅ All queries <100ms (p95)
- ✅ Redis caching (80% cache hit rate)
- ✅ Frontend bundle <500KB gzipped

#### **Success Metrics**

- API response time <500ms (p95)
- Time to Interactive (TTI) <3 seconds
- Cache hit rate >80%

---

### **Week 11: Security Hardening + GDPR Compliance**

#### **Objectives**

- Pass security audit (OWASP Top 10)
- Implement GDPR data controls
- Add audit logging

#### **Tasks**

**Day 1-2: Security Audit**

- [ ] Run OWASP ZAP scan (find vulnerabilities)
- [ ] Fix SQL injection risks (use parameterized queries)
- [ ] Fix XSS risks (sanitize user input)
- [ ] Implement rate limiting (prevent DDoS)

**Day 3-4: GDPR Compliance**

- [ ] Implement data export API (`/users/me/export`)
- [ ] Implement data deletion API (`/users/me/delete`)
- [ ] Add consent management (cookie banner)
- [ ] Encrypt PII at rest (database encryption)

**Day 5: Audit Logging**

- [ ] Log all sensitive operations (login, data access, changes)
- [ ] Store audit logs in immutable table (append-only)
- [ ] Implement log retention policy (7 years)

#### **Deliverables**

- ✅ Zero critical vulnerabilities (OWASP scan)
- ✅ GDPR-compliant data controls
- ✅ Audit logging for compliance

#### **Success Metrics**

- Security scan passes (0 critical, 0 high vulnerabilities)
- GDPR controls tested (export + deletion work)
- Audit logs capture all sensitive operations

---

### **Week 12: Beta Launch + Monitoring**

#### **Objectives**

- Launch beta with 10 SMBs
- Monitor production metrics
- Gather user feedback

#### **Tasks**

**Day 1-2: Beta Onboarding**

- [ ] Select 10 beta SMBs (diverse industries)
- [ ] Onboard them (create accounts, connect data sources)
- [ ] Train them on platform features (1-hour sessions)

**Day 3-4: Monitoring & Support**

- [ ] Set up alerts (Grafana alerting → Slack)
- [ ] Monitor error rates, latency, costs
- [ ] Provide support via Slack channel (respond <1 hour)

**Day 5: Retrospective**

- [ ] Collect user feedback (surveys, interviews)
- [ ] Document bugs and feature requests
- [ ] Plan next sprint priorities

#### **Deliverables**

- ✅ 10 beta SMBs actively using platform
- ✅ Production monitoring dashboards
- ✅ User feedback report

#### **Success Metrics**

- 8/10 beta SMBs actively engaged (>3 logins/week)
- Zero critical bugs in production
- User NPS score >40 (promoters - detractors)

---

## ✅ Success Criteria

### **Technical Success**

- [ ] Monolith handles 10,000 requests/sec (load test)
- [ ] PostgreSQL stores 1M+ rows (scalability test)
- [ ] AI coach responds <3 seconds (p95 latency)
- [ ] Optimization solves <5 seconds (typical SMB scale)
- [ ] Forecast accuracy (MAPE) <15%
- [ ] Infrastructure cost <$1/tenant/month
- [ ] System uptime >99.9% (production)

### **Business Success**

- [ ] 10 beta SMBs onboarded
- [ ] 8/10 SMBs actively engaged (>3 logins/week)
- [ ] User NPS score >40
- [ ] 5+ feature requests from users (product-market fit signal)
- [ ] Zero churn during beta (12 weeks)

### **Product Success**

- [ ] Coach handles 100+ conversations (diverse use cases)
- [ ] Optimization recommendations accepted >40% (user trust)
- [ ] Forecasts cited by users in planning (usefulness)
- [ ] Evidence explanations rated helpful >80%

---

## ⚠️ Risk Mitigation

### **Risk 1: Local LLM Accuracy Too Low**

- **Probability:** Medium
- **Impact:** High (user dissatisfaction)
- **Mitigation:**
  - Use larger local model (Llama 3 70B) if needed
  - Lower routing threshold (more queries go to cloud)
  - Fine-tune local model on SMB domain data

### **Risk 2: PostgreSQL Performance Bottleneck**

- **Probability:** Low
- **Impact:** Medium (slow queries)
- **Mitigation:**
  - Add read replicas (scale reads)
  - Use TimescaleDB compression (reduce storage)
  - Implement aggressive caching (Redis)

### **Risk 3: Beta SMBs Don't Engage**

- **Probability:** Medium
- **Impact:** High (no product feedback)
- **Mitigation:**
  - Incentivize participation (free months, discounts)
  - Provide white-glove onboarding (1:1 support)
  - Focus on SMBs with urgent pain points (high motivation)

### **Risk 4: Development Takes Longer Than 12 Weeks**

- **Probability:** Medium
- **Impact:** Medium (delayed launch)
- **Mitigation:**
  - Cut scope if needed (defer non-critical features)
  - Parallelize work (frontend + backend teams)
  - Use pre-built libraries (avoid custom implementations)

---

## 🎯 Next Steps

1. **Review this roadmap** with the team (align on priorities)
2. **Set up project tracking** (Jira, Linear, or GitHub Projects)
3. **Start Week 1** (monolith structure + PostgreSQL migration)
4. **Weekly check-ins** (adjust roadmap based on progress)

**Let's build! 🚀**
