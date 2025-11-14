# 🏛️ Service Architecture

**Version:** 4.0 (Modular Monolith)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [Architecture Evolution](#architecture-evolution)
2. [Modular Monolith Design](#modular-monolith-design)
3. [Service Modules](#service-modules)
4. [Module Communication](#module-communication)
5. [Directory Structure](#directory-structure)
6. [Deployment Model](#deployment-model)
7. [Migration Path](#migration-path)

---

## 🔄 Architecture Evolution

### **v1-3: 19 Microservices (Deprecated)**

```
SMB Gateway → Goal Service → Coach Service → Optimization Engine
                           ↓
           Forecasting ← Evidence ← Connector Service
                           ↓
           Analytics ← Notification ← ... (11 more services)
```

**Problems:**

- ❌ **High operational complexity** (19 deployments, 19 configs, 19 log streams)
- ❌ **Network overhead** (inter-service REST calls add 50-200ms latency)
- ❌ **Difficult debugging** (distributed tracing required, hard to reproduce issues)
- ❌ **Slow development** (coordinated releases, breaking changes across services)

---

### **v4.0: Modular Monolith (Current)**

```
┌────────────────────────────────────────────────┐
│         FastAPI Monolith (Single Process)      │
├────────────────────────────────────────────────┤
│ GoalService │ CoachService │ OptimizerService │
│ ForecastService │ EvidenceService │ etc.      │
└────────────────────────────────────────────────┘
              ↓ (Direct function calls)
      PostgreSQL (Single Database)
```

**Benefits:**

- ✅ **80% reduction in ops complexity** (1 deployment, 1 log stream, 1 config)
- ✅ **Zero network overhead** (in-memory function calls, <1ms)
- ✅ **Easy debugging** (single process, standard Python debugger works)
- ✅ **Fast iteration** (change multiple modules in one commit)
- ✅ **Cost-effective** (single VM scales to 5000 SMBs)

---

## 🧩 Modular Monolith Design

### **Design Principles**

1. **Domain-Driven Design (DDD)**
   - Each module owns a bounded context (Goals, Coach, Optimization, etc.)
   - Clear interfaces between modules (dependency injection)

2. **Loose Coupling**
   - Modules communicate via interfaces (not direct imports)
   - Changes to one module don't break others

3. **High Cohesion**
   - Related functionality grouped together
   - Each module has single responsibility

4. **Easy to Extract**
   - If scale demands, modules can become microservices later
   - Minimal code changes (interface → REST API)

---

## 🛠️ Service Modules

### **1. GoalService**

**Responsibility:** SMART goal lifecycle management

**Core Functions:**

- `create_goal(tenant_id, user_id, goal_data)` → Validate SMART criteria, store in DB
- `update_goal_progress(goal_id, metrics)` → Track progress, trigger alerts
- `evaluate_goal(goal_id)` → Assess achievement, generate insights
- `suggest_goals(tenant_id, business_context)` → AI-powered goal recommendations

**Tech Stack:** SQLAlchemy ORM, Pydantic validation

**Database Tables:**

- `smart_goals` (goal definitions, progress, status)
- `goal_milestones` (checkpoints along the way)

---

### **2. CoachService (Multi-Agent)**

**Responsibility:** Conversational AI coach

**Core Functions:**

- `ask_coach(query, context)` → Route to appropriate agent (Goal Planner, Forecaster, etc.)
- `stream_response(query)` → Server-Sent Events for real-time output
- `retrieve_context(query)` → RAG using pgvector for similar conversations

**Tech Stack:** LangGraph (state machines), LangChain (tools), Ollama/OpenAI (LLMs)

**Agents:**

1. **Goal Planner** → Decompose user intent into SMART goals
2. **Evidence Analyzer** → Explain why metrics changed (causal inference)
3. **Forecaster** → Predict future outcomes
4. **Optimizer** → Recommend optimal actions

**Database Tables:**

- `coaching_sessions` (conversation history + embeddings)
- `agent_executions` (trace which agents ran, what they returned)

---

### **3. OptimizerService**

**Responsibility:** Mathematical optimization for operations

**Core Functions:**

- `optimize_inventory(tenant_id, constraints)` → Minimize holding costs + stockouts
- `optimize_staffing(tenant_id, demand_forecast)` → Minimize labor costs, meet service levels
- `optimize_budget(tenant_id, channels)` → Maximize ROI across marketing channels

**Tech Stack:** OR-Tools (Google), PuLP (Python LP)

**Techniques:**

- Linear Programming (LP) for continuous decisions
- Mixed-Integer Programming (MILP) for discrete choices (hire 3 staff, not 3.5)
- Constraint Programming (CP) for complex scheduling

**Database Tables:**

- `optimization_runs` (inputs, outputs, solver metrics)
- `optimization_constraints` (business rules per tenant)

---

### **4. ForecasterService**

**Responsibility:** Time-series predictions with uncertainty

**Core Functions:**

- `forecast_metric(metric_name, horizon, confidence_level)` → Return point estimates + intervals
- `ensemble_forecast(metric_name)` → Combine ARIMA + Prophet + XGBoost
- `detect_anomalies(metric_name)` → Flag unusual values

**Tech Stack:** statsmodels (ARIMA), Prophet (Meta), XGBoost, scikit-learn

**Models:**

1. **Auto-ARIMA** → Automatic parameter selection for stationary series
2. **Prophet** → Handles seasonality, holidays, trend changes
3. **XGBoost** → Feature-based (lagged values, exogenous variables)
4. **Ensemble** → Weighted average (typically 70% accuracy improvement)

**Database Tables:**

- `forecasts` (predictions with confidence intervals)
- `forecast_models` (trained model metadata, performance metrics)

---

### **5. EvidenceService**

**Responsibility:** Causal inference and root cause analysis

**Core Functions:**

- `explain_change(metric_name, time_range)` → Identify causal factors
- `simulate_intervention(action, expected_impact)` → "What if we hire 2 more staff?"
- `build_causal_graph(tenant_id)` → Learn DAG from historical data

**Tech Stack:** DoWhy (Microsoft), pgmpy (Bayesian networks), CausalNex

**Methods:**

1. **Granger Causality** → Detect time-lagged relationships
2. **Propensity Score Matching** → Estimate causal effects from observational data
3. **Counterfactual Analysis** → Compare actual vs. hypothetical outcomes

**Database Tables:**

- `evidence_graph` (causal DAG as JSONB or Apache AGE graph)
- `causal_estimates` (effect sizes, confidence intervals, p-values)

---

### **6. ConnectorService**

**Responsibility:** Data ingestion from external sources

**Core Functions:**

- `connect_datasource(tenant_id, source_type, credentials)` → OAuth2 flow, store tokens
- `sync_data(connector_id)` → Fetch new/updated records
- `transform_data(raw_data, mapping)` → Normalize to internal schema

**Tech Stack:** Requests (HTTP client), OAuth2 libraries, Pandas (data transforms)

**Supported Connectors:**

- **Accounting:** QuickBooks, Xero, FreshBooks
- **E-commerce:** Shopify, WooCommerce, BigCommerce
- **CRM:** Salesforce, HubSpot, Pipedrive
- **Payments:** Stripe, Square, PayPal
- **Custom:** CSV/Excel upload, REST API webhooks

**Database Tables:**

- `data_sources` (connector configs, credentials, sync status)
- `connector_sync_logs` (history of syncs, errors)
- `raw_data_staging` (temporary storage before transformation)

---

### **7. AnalyticsService**

**Responsibility:** Query builder and metric aggregation

**Core Functions:**

- `query_metrics(tenant_id, filters, aggregations)` → Flexible SQL generation
- `create_dashboard(tenant_id, widgets)` → Save custom dashboard configs
- `export_data(query, format)` → CSV, Excel, JSON exports

**Tech Stack:** SQLAlchemy (query building), Pandas (aggregations)

**Database Tables:**

- `dashboards` (user-defined dashboard layouts)
- `saved_queries` (frequently used metric queries)

---

### **8. NotificationService**

**Responsibility:** Multi-channel alerts

**Core Functions:**

- `send_notification(tenant_id, user_id, message, channel)` → Email, Slack, in-app
- `schedule_notification(trigger, message)` → Weekly goal reminders
- `send_alert(condition, severity)` → Metric threshold breaches

**Tech Stack:** SMTP (email), Slack SDK, WebSockets (in-app)

**Channels:**

- **Email:** SMTP relay (SendGrid, Mailgun, or self-hosted Postfix)
- **Slack:** Webhook or OAuth app
- **In-App:** WebSocket push to frontend
- **Webhooks:** Custom HTTP callbacks

**Database Tables:**

- `notification_preferences` (user settings per channel)
- `notification_queue` (pending notifications, retry logic)

---

## 🔗 Module Communication

### **1. Direct Function Calls (Primary)**

```python
# Example: Coach calls Optimizer
from services.optimizer_service import OptimizerService
from services.coach_service import CoachService

class CoachService:
    def __init__(self, optimizer: OptimizerService):
        self.optimizer = optimizer  # Dependency injection
    
    async def handle_query(self, query: str):
        if "optimize inventory" in query.lower():
            result = await self.optimizer.optimize_inventory(...)
            return self.format_response(result)
```

**Benefits:**

- ⚡ **Fast:** In-memory calls (<1ms overhead)
- 🐛 **Easy to debug:** Standard Python debugger works
- 🔒 **Type-safe:** mypy catches errors at compile time

---

### **2. Database as Integration Point (Secondary)**

For asynchronous workflows:

```python
# Module A writes to database
await db.execute("INSERT INTO tasks (type, payload) VALUES ('forecast', $1)", payload)

# Module B listens via PostgreSQL LISTEN/NOTIFY
await db.execute("LISTEN task_queue")
async for notification in db.notifications():
    if notification.channel == "task_queue":
        process_task(notification.payload)
```

---

### **3. Event Bus (Optional for Complex Flows)**

For decoupled pub/sub:

```python
from events import EventBus

# Publisher
await event_bus.publish("goal.completed", {"goal_id": "123", "outcome": "achieved"})

# Subscriber (in another module)
@event_bus.subscribe("goal.completed")
async def on_goal_completed(event):
    await notification_service.send_congratulations(event["goal_id"])
```

---

## 📁 Directory Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── config.py                  # Environment variables, settings
├── dependencies.py            # Dependency injection setup
│
├── routes/                    # API endpoints (thin layer)
│   ├── auth.py               # POST /auth/login, /auth/logout
│   ├── goals.py              # CRUD for /goals/*
│   ├── coach.py              # POST /coach/ask (streaming)
│   ├── optimize.py           # POST /optimize/{type}
│   ├── forecast.py           # GET /forecast/{metric}
│   └── evidence.py           # GET /evidence/explain
│
├── services/                  # Business logic (thick layer)
│   ├── __init__.py
│   ├── goal_service.py       # GoalService class
│   ├── coach_service.py      # CoachService class
│   ├── optimizer_service.py  # OptimizerService class
│   ├── forecaster_service.py # ForecasterService class
│   ├── evidence_service.py   # EvidenceService class
│   ├── connector_service.py  # ConnectorService class
│   ├── analytics_service.py  # AnalyticsService class
│   └── notification_service.py # NotificationService class
│
├── agents/                    # LangGraph agent definitions
│   ├── goal_planner.py       # Goal decomposition agent
│   ├── evidence_analyzer.py  # Causal explanation agent
│   ├── forecaster_agent.py   # Prediction agent
│   └── optimizer_agent.py    # Recommendation agent
│
├── models/                    # SQLAlchemy ORM models
│   ├── tenant.py
│   ├── user.py
│   ├── goal.py
│   ├── metric.py
│   ├── session.py
│   └── connector.py
│
├── schemas/                   # Pydantic request/response models
│   ├── goal_schemas.py
│   ├── coach_schemas.py
│   └── optimization_schemas.py
│
├── utils/                     # Helpers
│   ├── auth.py               # JWT token management
│   ├── logging.py            # Structured logging
│   ├── metrics.py            # Prometheus instrumentation
│   └── cache.py              # Redis caching
│
└── tests/                     # Unit + integration tests
    ├── unit/
    │   ├── test_goal_service.py
    │   └── test_coach_service.py
    └── integration/
        └── test_coach_optimization_flow.py
```

---

## 🚀 Deployment Model

### **Development (Docker Compose)**

```yaml
version: '3.8'
services:
  postgres:
    image: timescale/timescaledb-ha:pg16
    ports: ["5432:5432"]
  
  backend:
    build: ./backend
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ports: ["8000:8000"]
    depends_on: [postgres]
  
  frontend:
    build: ./apps/smb
    command: npm run dev
    ports: ["3000:3000"]
```

**Start:** `docker-compose up -d`

---

### **Production (Single VM, <5000 SMBs)**

```bash
# 1. Build backend
cd backend && docker build -t dyocense-backend .

# 2. Run with systemd
sudo systemctl start dyocense-backend

# 3. Reverse proxy (Nginx)
sudo nginx -s reload  # Routes traffic to backend:8000
```

**Vertical Scaling:** 16 vCPU, 64GB RAM → handles 5000 SMBs

---

### **Scale (Kubernetes, >5000 SMBs)**

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dyocense-backend
spec:
  replicas: 5  # Horizontal scaling
  template:
    spec:
      containers:
      - name: backend
        image: dyocense-backend:latest
        resources:
          requests: {cpu: "2", memory: "4Gi"}
```

**Database:** PostgreSQL with read replicas (scale reads)

---

## 🔄 Migration Path

### **From Microservices to Monolith**

**Phase 1: Consolidate Shared Libraries**

1. Extract common code (auth, logging, metrics) into `utils/`
2. Remove duplicated code across old services

**Phase 2: Merge Services into Modules**

1. Copy `services/goal_service/main.py` → `backend/services/goal_service.py`
2. Convert REST APIs to function calls
3. Update imports (remove network clients)

**Phase 3: Unify Database Access**

1. Merge schemas into single Alembic migration directory
2. Apply Row-Level Security (RLS) policies
3. Remove per-service database users (use single app user)

**Phase 4: Update Deployment**

1. Replace 19 Docker containers with 1
2. Simplify CI/CD (single build/deploy pipeline)
3. Update monitoring (1 target instead of 19)

**Phase 5: Test & Validate**

1. Run integration tests (verify no regressions)
2. Load test (ensure performance meets SLAs)
3. Beta deploy (10 SMBs for 1 week)

---

## 🎯 Next Steps

1. **Review [Design Document](./Design-Document.md)** for overall architecture
2. **Review [Data Architecture](./Data-Architecture.md)** for PostgreSQL schema
3. **Start Phase 0** of [Implementation Roadmap](./Implementation-Roadmap.md)

**Ready to build! 🚀**
