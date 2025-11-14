# 📐 Design Document

**Version:** 4.0 (Cost-Optimized Monolith)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [High-Level Architecture Diagram](#high-level-architecture-diagram)
3. [Design Principles](#design-principles)
4. [Component Details](#component-details)
5. [Data Model](#data-model)
6. [API Design](#api-design)
7. [Security Architecture](#security-architecture)
8. [Scalability Strategy](#scalability-strategy)

---

## 🎯 System Architecture Overview

### **What Changed in v4.0?**

| Aspect | v3.0 (Microservices) | v4.0 (Monolith) | Impact |
|--------|---------------------|----------------|--------|
| **Services** | 19 microservices | 1 FastAPI monolith | 80% ops reduction |
| **Databases** | 4 (PostgreSQL, Vector, Graph, Redis) | 1 (PostgreSQL) | $700/mo savings |
| **Deployment** | Kubernetes (complex) | Docker Compose (simple) | 96% faster deploys |
| **LLM Strategy** | 100% cloud | 70% local, 30% cloud | 80% cost reduction |
| **Infrastructure Cost** | $5/tenant/mo | <$1/tenant/mo | 80% savings |

### **Why Simplify?**

1. **Premature Optimization:** 19 microservices was overkill for 0-5000 SMBs
2. **Operational Overhead:** Managing 19 deployments, 19 log streams, 19 configs
3. **Cost Unpredictability:** Per-request pricing for specialized databases
4. **Development Velocity:** Coordinated releases across services slowed iteration

### **Target Scale**

- **Phase 1 (Bootstrap):** 1-50 SMBs → Single VM ($55/mo)
- **Phase 2 (Growth):** 50-500 SMBs → Larger VM ($280/mo)
- **Phase 3 (Scale):** 500-5000 SMBs → Kubernetes cluster ($1500-3000/mo)

---

## 🏗️ High-Level Architecture Diagram

### **Simplified Monolithic Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  SMB Web Portal (Next.js/React)                                 │
│  - Dashboard (goals, metrics, insights)                         │
│  - AI Coach Chat Interface (streaming responses)                │
│  - Data Connectors Management                                   │
│  - Settings & Account Management                                │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS (JWT Auth)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND MONOLITH (FastAPI)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ API Layer (FastAPI Routes)                              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ /auth/*     → Login, logout, token refresh              │   │
│  │ /goals/*    → SMART goal CRUD, tracking                 │   │
│  │ /coach/*    → AI coach conversations (streaming SSE)    │   │
│  │ /optimize/* → Optimization requests (inventory, staff)  │   │
│  │ /forecast/* → Time-series predictions                   │   │
│  │ /evidence/* → Causal explanations                       │   │
│  │ /metrics/*  → Business metric queries                   │   │
│  │ /connect/*  → Data source integrations                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Business Logic Layer (Services)                         │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • GoalService    → Goal lifecycle, SMART validation     │   │
│  │ • CoachService   → Multi-agent orchestration (LangGraph)│   │
│  │ • OptimizerService → LP solvers (OR-Tools, PuLP)        │   │
│  │ • ForecasterService → ARIMA, Prophet, XGBoost ensemble  │   │
│  │ • EvidenceService → Causal inference (DoWhy, pgmpy)     │   │
│  │ • ConnectorService → Data ingestion from external APIs  │   │
│  │ • NotificationService → Email, Slack, in-app alerts     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Data Access Layer (SQLAlchemy ORM)                      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ • Models (Tenants, Users, Goals, Metrics, Sessions)     │   │
│  │ • Row-Level Security (RLS) Middleware                   │   │
│  │ • Query Optimization (eager loading, caching)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            POSTGRESQL 16+ (Single Database)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Extensions:                                                     │
│  ├─ TimescaleDB → Time-series metrics (hypertables)             │
│  ├─ pgvector   → Vector search for RAG (384-dim embeddings)     │
│  ├─ Apache AGE → Graph queries for causal evidence              │
│  ├─ pg_cron    → Scheduled jobs (data refresh, aggregations)    │
│                                                                  │
│  Core Tables:                                                    │
│  ├─ tenants (companies)                                          │
│  ├─ users (SMB employees)                                        │
│  ├─ smart_goals (goal lifecycle tracking)                        │
│  ├─ business_metrics (TimescaleDB hypertable)                    │
│  ├─ coaching_sessions (chat history + embeddings)                │
│  ├─ evidence_graph (causal DAG as JSONB or AGE graph)            │
│  ├─ data_sources (connector configurations)                      │
│  ├─ external_benchmarks (industry data from FRED, IBISWorld)     │
│  ├─ forecasts (predicted metrics with confidence intervals)      │
│  └─ optimization_runs (inventory, staffing, budget solutions)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│               OBSERVABILITY STACK (Open Source)                  │
├─────────────────────────────────────────────────────────────────┤
│  • Prometheus → Metrics (request rate, latency, costs)          │
│  • Grafana    → Dashboards (system health, business KPIs)       │
│  • Loki       → Structured logging (JSON logs, searchable)      │
│  • Jaeger     → Distributed tracing (request flow)              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SYSTEMS                            │
├─────────────────────────────────────────────────────────────────┤
│  • Local LLM (Llama 3 8B via Ollama) → 70% of queries           │
│  • Cloud LLMs (OpenAI GPT-4o, Claude) → 30% of queries          │
│  • Data Sources (ERPNext, QuickBooks, Shopify, Stripe)          │
│  • Benchmark APIs (FRED, IBISWorld, Census Bureau)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧭 Design Principles

### **1. PostgreSQL-First Architecture**

> **"One database to rule them all"**

- **Single Source of Truth:** All data in PostgreSQL (relational, time-series, vector, graph)
- **ACID Guarantees:** Critical business data gets transactional consistency
- **Operational Simplicity:** One database to backup, monitor, scale

### **2. Modular Monolith**

> **"Organized as microservices, deployed as monolith"**

- **Domain-Driven Design:** Clear boundaries (GoalService, CoachService, etc.)
- **Loose Coupling:** Services interact via interfaces (dependency injection)
- **Easy to Split:** If scale demands, extract services later

### **3. Hybrid Intelligence**

> **"LLMs for language, optimization for decisions"**

- **LLMs (70% local, 30% cloud):** Natural language understanding, explanations
- **Optimization (OR-Tools):** Mathematically optimal decisions (inventory, staffing)
- **Forecasting (Prophet, ARIMA):** Quantified uncertainty (confidence intervals)
- **Causal Inference (DoWhy):** Explain "why" metrics changed

### **4. Tenant Isolation via Row-Level Security (RLS)**

> **"Fortress at the database layer"**

- **PostgreSQL RLS Policies:** Enforce `tenant_id` filtering in database
- **No Application-Level Bugs:** Even buggy code can't leak data
- **Middleware Sets Context:** Every request sets `app.current_tenant` session variable

### **5. Cost-Optimized by Default**

> **"Every feature must justify its cost"**

- **No Specialized Databases:** PostgreSQL extensions over separate databases
- **Vertical Scaling First:** Single VM scales to 5000 SMBs
- **Local LLMs:** 80% cost reduction vs. cloud-only
- **Open-Source Only:** Zero licensing fees

### **6. Observability from Day One**

> **"You can't improve what you don't measure"**

- **Instrumented APIs:** Prometheus metrics on every endpoint
- **Structured Logs:** JSON logs with trace IDs (correlation)
- **Cost Tracking:** Monitor LLM spend, infrastructure costs per tenant
- **Alerting:** Slack alerts for errors, high latency, budget overruns

---

## 🧩 Component Details

### **1. API Layer (FastAPI Routes)**

**Responsibilities:**

- HTTP request/response handling
- JWT authentication & authorization
- Input validation (Pydantic schemas)
- Rate limiting (per tenant)
- Request logging & tracing

**Example Route:**

```python
from fastapi import APIRouter, Depends
from schemas import GoalCreate, GoalResponse
from services.goal_service import GoalService
from dependencies import get_current_user, get_tenant_context

router = APIRouter(prefix="/goals", tags=["goals"])

@router.post("/", response_model=GoalResponse)
async def create_goal(
    goal: GoalCreate,
    user = Depends(get_current_user),
    tenant_id = Depends(get_tenant_context),
    service: GoalService = Depends()
):
    return await service.create_goal(tenant_id, user.id, goal)
```

---

### **2. Business Logic Layer (Services)**

#### **GoalService**

- SMART goal validation (Specific, Measurable, Achievable, Relevant, Time-bound)
- Goal lifecycle management (created → in_progress → completed → archived)
- Progress tracking (metric-based evaluation)

#### **CoachService (Multi-Agent)**

- LangGraph state machine for conversation flow
- Agents: Goal Planner, Evidence Analyzer, Forecaster, Optimizer
- Streaming responses (Server-Sent Events for real-time output)
- Context retrieval (RAG using pgvector for similar conversations)

#### **OptimizerService**

- Linear programming models (inventory, staffing, budget allocation)
- Constraint validation (business rules, capacity limits)
- Solution interpretation (generate human-readable recommendations)

#### **ForecasterService**

- Auto-ARIMA (automatic parameter selection)
- Prophet (seasonality, holidays, trend detection)
- XGBoost (feature-based forecasting with lagged variables)
- Ensemble (weighted average of all models)

#### **EvidenceService**

- Bayesian network learning (structure + parameters)
- Granger causality tests (time-lagged relationships)
- Counterfactual reasoning ("what if" scenarios)
- Causal graph storage (PostgreSQL JSONB or Apache AGE)

#### **ConnectorService**

- OAuth2 flows for external APIs (QuickBooks, Shopify, Stripe)
- Data extraction & transformation
- Incremental sync (only fetch new/changed data)
- Error handling & retry logic

---

### **3. Data Access Layer (SQLAlchemy ORM)**

**Row-Level Security Middleware:**

```python
from sqlalchemy import event
from sqlalchemy.orm import Session

@event.listens_for(Session, "after_begin")
def set_tenant_context(session, transaction, connection):
    tenant_id = get_current_tenant_id()  # From request context
    connection.execute(f"SET app.current_tenant = '{tenant_id}'")
```

**PostgreSQL RLS Policy:**

```sql
CREATE POLICY tenant_isolation ON business_metrics
USING (tenant_id = current_setting('app.current_tenant')::uuid);

ALTER TABLE business_metrics ENABLE ROW LEVEL SECURITY;
```

---

## 🗂️ Data Model

### **Core Entities**

#### **Tenants (Companies)**

```sql
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  industry TEXT, -- 'restaurant', 'retail', 'healthcare', etc.
  created_at TIMESTAMPTZ DEFAULT NOW(),
  subscription_tier TEXT DEFAULT 'starter', -- 'starter', 'pro', 'enterprise'
  is_active BOOLEAN DEFAULT true
);
```

#### **Users (SMB Employees)**

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT DEFAULT 'member', -- 'admin', 'manager', 'member'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```

#### **SMART Goals**

```sql
CREATE TABLE smart_goals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id),
  user_id UUID REFERENCES users(id),
  title TEXT NOT NULL,
  description TEXT,
  target_metric TEXT, -- 'revenue', 'customer_count', 'inventory_turnover'
  target_value NUMERIC,
  current_value NUMERIC,
  deadline TIMESTAMPTZ,
  status TEXT DEFAULT 'in_progress', -- 'created', 'in_progress', 'completed', 'archived'
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE smart_goals ENABLE ROW LEVEL SECURITY;
```

#### **Business Metrics (TimescaleDB Hypertable)**

```sql
CREATE TABLE business_metrics (
  time TIMESTAMPTZ NOT NULL,
  tenant_id UUID NOT NULL,
  metric_name TEXT NOT NULL, -- 'revenue', 'sales_count', 'inventory_level'
  value NUMERIC NOT NULL,
  unit TEXT, -- 'USD', 'count', 'units'
  metadata JSONB, -- Flexible additional context
  PRIMARY KEY (time, tenant_id, metric_name)
);

SELECT create_hypertable('business_metrics', 'time');
ALTER TABLE business_metrics ENABLE ROW LEVEL SECURITY;
```

#### **Coaching Sessions (with Embeddings)**

```sql
CREATE EXTENSION vector;

CREATE TABLE coaching_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id),
  user_id UUID REFERENCES users(id),
  user_query TEXT NOT NULL,
  query_embedding vector(384), -- Sentence Transformers all-MiniLM-L6-v2
  coach_response TEXT NOT NULL,
  llm_provider TEXT, -- 'local_llama3' or 'openai_gpt4o'
  response_time_ms INT,
  cost_usd NUMERIC(10, 6),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_embedding ON coaching_sessions 
USING ivfflat (query_embedding vector_cosine_ops);

ALTER TABLE coaching_sessions ENABLE ROW LEVEL SECURITY;
```

#### **Evidence Graph (Causal Relationships)**

```sql
CREATE TABLE evidence_graph (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id),
  graph_data JSONB NOT NULL, -- Nodes + edges as JSON
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE evidence_graph ENABLE ROW LEVEL SECURITY;
```

---

## 🔌 API Design

### **RESTful Conventions**

- **GET** `/goals` → List all goals (paginated)
- **POST** `/goals` → Create new goal
- **GET** `/goals/{id}` → Get goal details
- **PUT** `/goals/{id}` → Update goal
- **DELETE** `/goals/{id}` → Archive goal

### **Streaming Endpoints (Server-Sent Events)**

```python
@router.post("/coach/ask", response_class=StreamingResponse)
async def ask_coach(query: str):
    async def event_stream():
        async for chunk in coach_service.stream_response(query):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### **Pagination & Filtering**

```python
@router.get("/goals", response_model=List[GoalResponse])
async def list_goals(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    tenant_id = Depends(get_tenant_context)
):
    return await goal_service.list_goals(tenant_id, skip, limit, status)
```

---

## 🔒 Security Architecture

### **Authentication (JWT)**

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return await get_user_by_id(payload["user_id"])
```

### **Row-Level Security (RLS) Enforcement**

Every database query automatically filtered by `tenant_id`:

```sql
-- User tries to query: SELECT * FROM business_metrics;
-- PostgreSQL executes: SELECT * FROM business_metrics WHERE tenant_id = 'abc-123';
```

### **Data Encryption**

- **In Transit:** HTTPS only (TLS 1.3)
- **At Rest:** PostgreSQL encryption (LUKS for disk, transparent column encryption for PII)

---

## 📈 Scalability Strategy

### **Vertical Scaling (Phase 1-2: 0-5000 SMBs)**

- Single VM: 16 vCPU, 64GB RAM
- PostgreSQL connection pooling (pgBouncer)
- Redis for LLM response caching

### **Horizontal Scaling (Phase 3: >5000 SMBs)**

- **Backend:** Multiple FastAPI instances (load balanced)
- **Database:** PostgreSQL read replicas (scale reads)
- **Caching:** Redis cluster (high availability)

### **Database Optimization**

- **Partitioning:** TimescaleDB automatic time-based partitioning
- **Compression:** 90% reduction for historical metrics
- **Indexes:** B-tree, GIN (JSONB), BRIN (time-series), IVFFlat (vectors)

---

## 🎯 Next Steps

1. **Review [Implementation Roadmap](./Implementation-Roadmap.md)** for 12-week execution plan
2. **Deep-dive into specific architectures:**
   - [Service Architecture](./Service-Architecture.md)
   - [Data Architecture](./Data-Architecture.md)
   - [AI & Analytics Stack](./AI & Analytics Stack.md)
3. **Start development** (follow [00-READ-ME-FIRST.md](./00-READ-ME-FIRST.md))
