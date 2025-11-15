# 🛠️ Technology Stack Selection

**Version:** 4.0 (Cost-Optimized Monolith)  
**Last Updated:** November 14, 2025  
**Status:** Active Development

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Core Technologies](#core-technologies)
3. [Database Layer](#database-layer)
4. [Backend Framework](#backend-framework)
5. [AI & ML Stack](#ai--ml-stack)
6. [Observability Stack](#observability-stack)
7. [Deployment Architecture](#deployment-architecture)
8. [Technology Trade-offs](#technology-trade-offs)
9. [Conclusion](#conclusion)

---

## 🎯 Overview

### **Guiding Principles**

1. **PostgreSQL-First:** Use a single database for all workloads (relational, time-series, vector, graph)
2. **Open-Source Only:** No vendor lock-in, portable across clouds
3. **Cost-Optimized:** Target <$1/tenant/month infrastructure costs
4. **Simplicity:** Monolithic architecture until scale demands otherwise
5. **Hybrid AI:** Combine local LLMs (70%) + cloud LLMs (30%) for cost efficiency

### **Architecture Philosophy**

> **"Start with a monolith, add complexity only when necessary."**

Unlike v1-3 (19 microservices), v4.0 consolidates into a single FastAPI backend. This reduces:

- **Operational complexity** (80% reduction)
- **Infrastructure costs** ($5/tenant → <$1/tenant)
- **Development velocity** (single deployment pipeline)

---

## 🗂️ Core Technologies

### **Quick Reference Table**

| Layer | Technology | Rationale | Cost Savings |
|-------|-----------|-----------|--------------|
| **Database** | PostgreSQL 16+ | Single DB for all workloads, ACID guarantees | N/A (baseline) |
| **Time-Series** | TimescaleDB | Native PostgreSQL extension, compression | Replaces InfluxDB ($200/mo) |
| **Vector Search** | pgvector | Semantic search in PostgreSQL | Replaces Pinecone ($200/mo) |
| **Graph Queries** | Apache AGE | Cypher queries in PostgreSQL | Replaces Neo4j ($500/mo) |
| **API Framework** | FastAPI | Async, auto-docs, Pydantic validation | N/A |
| **LLM Orchestration** | LangGraph | State machines for agents, streaming | N/A |
| **Optimization** | OR-Tools, PuLP | Industry-standard linear programming | N/A |
| **Forecasting** | Prophet, ARIMA, XGBoost | Battle-tested time-series models | N/A |
| **Causal Inference** | DoWhy, pgmpy | Research-backed causal AI | N/A |
| **Tracing** | OpenTelemetry + Jaeger | Vendor-neutral, CNCF standard | N/A |
| **Metrics** | Prometheus + Grafana | De facto standard observability | Replaces Datadog ($500/mo) |
| **Logging** | Loki | Lightweight, integrates with Grafana | Replaces Datadog ($200/mo) |
| **Container Runtime** | Docker Compose | Simple, scales to 5000 SMBs | Replaces Kubernetes ($800/mo) |
| **CI/CD** | GitHub Actions | Native to repo, free tier | N/A |

**Total Monthly Savings:** $2,400/month (from specialized SaaS → open-source)

---

## 🗄️ Database Layer

### **PostgreSQL 16+ (Single Source of Truth)**

**Why PostgreSQL?**

- **Mature & Stable:** 30+ years of development, ACID compliant
- **Extensible:** Add time-series, vector, graph capabilities without new databases
- **Cost-Effective:** Free, runs on any cloud or on-premise
- **Multi-Cloud:** No vendor lock-in (AWS RDS, Azure PostgreSQL, GCP Cloud SQL, self-hosted)

**Key Features:**

- Row-Level Security (RLS) for multi-tenancy
- JSONB for semi-structured data (flexible schemas)
- Full-text search (no need for Elasticsearch)
- Partitioning for large tables (100M+ rows)
- LISTEN/NOTIFY for pub/sub (no need for Redis Streams)

---

### **TimescaleDB (Time-Series Extension)**

**Why TimescaleDB?**

- **Native PostgreSQL Extension:** No separate database
- **Automatic Compression:** 90% storage reduction for time-series data
- **Continuous Aggregates:** Pre-computed rollups (hourly, daily, monthly)
- **Hypertables:** Automatic partitioning by time

**Use Cases:**

- Store business metrics (revenue, sales, inventory levels)
- Track goal progress over time
- Monitor system performance (API latency, error rates)

**Example Schema:**

```sql
CREATE TABLE business_metrics (
  time TIMESTAMPTZ NOT NULL,
  tenant_id UUID NOT NULL,
  metric_name TEXT NOT NULL,
  value NUMERIC NOT NULL,
  metadata JSONB
);

SELECT create_hypertable('business_metrics', 'time');
```

---

### **pgvector (Vector Search Extension)**

**Why pgvector?**

- **Semantic Search:** Embed user queries, find similar conversations/data
- **RAG (Retrieval-Augmented Generation):** Retrieve relevant context for LLMs
- **No Separate Vector DB:** Avoid Pinecone ($200/mo), Weaviate, Qdrant costs

**Use Cases:**

- Find similar coaching sessions (for personalized recommendations)
- Semantic search over business documents
- Cluster similar goals/tasks (identify patterns)

**Example Schema:**

```sql
CREATE EXTENSION vector;

CREATE TABLE coaching_sessions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  user_query TEXT NOT NULL,
  embedding vector(384), -- Sentence Transformers dimension
  coach_response TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON coaching_sessions USING ivfflat (embedding vector_cosine_ops);
```

---

### **Apache AGE (Graph Queries Extension)**

**Why Apache AGE?**

- **Cypher Queries in PostgreSQL:** No need for separate Neo4j
- **Causal Graphs:** Model relationships between metrics (evidence engine)
- **Graph Analytics:** Find root causes, identify feedback loops

**Use Cases:**

- Evidence graphs (causal relationships between business metrics)
- Goal dependency tracking (prerequisite goals)
- Business entity relationships (suppliers → products → sales)

**Example Query:**

```sql
SELECT * FROM cypher('evidence_graph', $$
  MATCH (m1:Metric)-[:CAUSES]->(m2:Metric)
  WHERE m1.name = 'marketing_spend'
  RETURN m2.name, m2.impact_coefficient
$$) AS (metric_name TEXT, coefficient NUMERIC);
```

---

### **pg_cron (Scheduled Jobs Extension)**

**Why pg_cron?**

- **Built-in Scheduler:** No need for separate cron daemon or Airflow for simple jobs
- **Database-Native:** Runs inside PostgreSQL, no external dependencies

**Use Cases:**

- Refresh external benchmark data (daily)
- Recompute aggregates (hourly rollups)
- Send scheduled notifications (weekly goal reminders)

**Example:**

```sql
SELECT cron.schedule('refresh-benchmarks', '0 2 * * *', $$
  CALL refresh_external_benchmarks();
$$);
```

---

## ⚙️ Backend Framework

### **FastAPI (Python 3.11+)**

**Why FastAPI?**

- **High Performance:** Async/await, comparable to Node.js/Go
- **Automatic API Docs:** OpenAPI/Swagger out of the box
- **Type Safety:** Pydantic for request/response validation
- **Ecosystem:** Rich Python ML/AI libraries (Prophet, OR-Tools, LangChain)

**Key Libraries:**

- **SQLAlchemy 2.0:** ORM for PostgreSQL (async support)
- **Alembic:** Database migrations (version-controlled schema)
- **Pydantic:** Data validation and serialization
- **python-multipart:** File uploads (CSV, Excel)
- **httpx:** Async HTTP client (for external APIs)

**Example API Structure:**

```
backend/
├── main.py              # FastAPI app entry point
├── dependencies.py      # Dependency injection (DB, auth, tenant context)
├── models/              # SQLAlchemy models (tenants, users, goals, metrics)
├── routes/              # API endpoints (grouped by domain)
│   ├── auth.py         # Login, logout, token refresh
│   ├── goals.py        # CRUD for SMART goals
│   ├── coach.py        # AI coach conversations (streaming)
│   ├── optimize.py     # Optimization requests
│   ├── forecast.py     # Forecasting requests
│   └── evidence.py     # Causal explanations
├── services/            # Business logic (modular, reusable)
│   ├── coach/          # Multi-agent coach (LangGraph)
│   ├── optimizer/      # Mathematical optimization (OR-Tools)
│   ├── forecaster/     # Time-series forecasting (Prophet, ARIMA)
│   ├── evidence/       # Causal inference (DoWhy)
│   └── connectors/     # Data ingestion (ERPNext, QuickBooks, etc.)
├── agents/              # LangGraph agent definitions
├── schemas/             # Pydantic request/response models
└── utils/               # Helpers (logging, metrics, auth)
```

---

## 🤖 AI & ML Stack

### **Hybrid LLM Approach (70% Local, 30% Cloud)**

**Why Hybrid?**

- **Cost Savings:** 80% reduction vs. cloud-only ($0.50/100 queries vs. $2.50)
- **Privacy:** Sensitive SMB data stays local
- **Speed:** Local inference <500ms latency

**LLM Routing Logic:**

```python
def route_llm_query(query: str, context: dict) -> LLMProvider:
    complexity_score = estimate_complexity(query)
    
    if complexity_score < 0.3:
        return LocalLlama3_8B()  # 70% of queries
    else:
        return OpenAIGPT4o()     # 30% of queries
```

---

### **Local LLMs (Ollama or vLLM)**

**Model:** Llama 3 8B (quantized to 4-bit for efficiency)

**Deployment:**

- **Development:** Ollama (easy setup, auto-downloads models)
- **Production:** vLLM (optimized inference, batching, KV cache)

**Hardware Requirements:**

- **CPU:** 8+ cores
- **RAM:** 16GB+ (8B model needs ~6GB)
- **GPU:** Optional (speeds up inference 5-10x)

**Example Usage:**

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3", temperature=0.3)
response = llm.invoke("What's my revenue trend?")
```

---

### **Cloud LLMs (OpenAI GPT-4o, Anthropic Claude)**

**When to Use:**

- Complex reasoning (multi-step analysis)
- Creative tasks (generate marketing copy)
- Uncertainty (query ambiguity requires clarification)

**Cost Optimization:**

- Cache LLM responses (Redis, 24-hour TTL)
- Use smaller models (GPT-4o-mini for simple tasks)
- Batch requests (reduce per-request overhead)

**Example Usage:**

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
response = llm.invoke("Generate 3 revenue growth strategies for a restaurant.")
```

---

### **LangGraph (Agent Orchestration)**

**Why LangGraph?**

- **State Machines:** Explicit control flow (better than LangChain chains)
- **Streaming:** Real-time output (SSE for frontend)
- **Debugging:** Visualize agent state transitions

**Agent Architecture:**

```python
from langgraph.graph import StateGraph, END

# Define agent state
class CoachState(TypedDict):
    user_query: str
    conversation_history: List[Message]
    retrieved_context: str
    optimization_result: Optional[dict]
    forecast_result: Optional[dict]
    evidence_result: Optional[dict]
    final_response: str

# Define agent nodes
def retrieve_context(state): ...
def run_optimization(state): ...
def run_forecast(state): ...
def explain_evidence(state): ...
def generate_response(state): ...

# Build graph
workflow = StateGraph(CoachState)
workflow.add_node("retrieve", retrieve_context)
workflow.add_node("optimize", run_optimization)
workflow.add_node("forecast", run_forecast)
workflow.add_node("evidence", explain_evidence)
workflow.add_node("respond", generate_response)

# Define routing logic
workflow.add_conditional_edges("retrieve", route_to_tools)
workflow.add_edge("optimize", "respond")
workflow.add_edge("forecast", "respond")
workflow.add_edge("evidence", "respond")
workflow.add_edge("respond", END)

app = workflow.compile()
```

---

### **Optimization (OR-Tools, PuLP)**

**Why OR-Tools?**

- **Industry Standard:** Used by Google, Uber, DoorDash
- **Fast:** Optimized C++ solvers (SCIP, GLOP, CP-SAT)
- **Flexible:** Linear programming, constraint programming, routing

**Use Cases:**

- Inventory optimization (minimize holding costs + stockouts)
- Staffing optimization (minimize labor cost, meet service levels)
- Budget allocation (maximize ROI across channels)

**Example (Inventory Optimization):**

```python
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')

# Decision variables: order quantities for each product
order_qty = {p: solver.NumVar(0, solver.infinity(), f'order_{p}') 
             for p in products}

# Objective: minimize total cost
solver.Minimize(
    sum(holding_cost[p] * order_qty[p] for p in products) +
    sum(stockout_penalty[p] * max(0, demand[p] - order_qty[p]) for p in products)
)

# Constraints
solver.Add(sum(order_qty[p] * volume[p] for p in products) <= warehouse_capacity)

status = solver.Solve()
```

---

### **Forecasting (ARIMA, Prophet, XGBoost)**

**Why Multiple Models?**

- **Ensemble:** Average predictions for robustness
- **Different Strengths:** ARIMA (stationary), Prophet (seasonality), XGBoost (features)

**Auto-ARIMA (statsmodels):**

```python
from statsmodels.tsa.arima.model import ARIMA
from pmdarima import auto_arima

model = auto_arima(sales_data, seasonal=True, m=12)
forecast = model.predict(n_periods=30)
```

**Prophet (Meta):**

```python
from prophet import Prophet

df = pd.DataFrame({'ds': dates, 'y': sales})
model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
model.fit(df)
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)
```

**XGBoost (Feature-Based):**

```python
from xgboost import XGBRegressor

X_train = create_features(sales_data)  # lag features, rolling stats
y_train = sales_data['revenue']
model = XGBRegressor(n_estimators=100)
model.fit(X_train, y_train)
forecast = model.predict(X_test)
```

---

### **Causal Inference (DoWhy, pgmpy)**

**Why Causal AI?**

- **Explain "Why":** Not just correlation, but causation
- **Counterfactuals:** "What if we had increased marketing by 20%?"
- **Patentable IP:** Unique differentiator vs. BI tools

**DoWhy (Microsoft Research):**

```python
from dowhy import CausalModel

model = CausalModel(
    data=business_data,
    treatment='marketing_spend',
    outcome='revenue',
    common_causes=['seasonality', 'competitor_activity']
)

identified_estimand = model.identify_effect()
estimate = model.estimate_effect(identified_estimand)
print(f"Causal effect: ${estimate.value} revenue per $1 marketing")
```

**pgmpy (Bayesian Networks):**

```python
from pgmpy.models import BayesianNetwork
from pgmpy.estimators import MaximumLikelihoodEstimator

model = BayesianNetwork([
    ('marketing_spend', 'website_traffic'),
    ('website_traffic', 'leads'),
    ('leads', 'revenue')
])

model.fit(data, estimator=MaximumLikelihoodEstimator)
model.predict(pd.DataFrame({'marketing_spend': [5000]}))
```

---

## 📊 Observability Stack

### **Prometheus (Metrics)**

**Why Prometheus?**

- **Pull-Based:** Scrapes metrics from FastAPI
- **Time-Series DB:** Built-in storage for metrics history
- **Alerting:** Prometheus Alertmanager for Slack/email alerts

**FastAPI Instrumentation:**

```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

**Key Metrics:**

- Request rate (requests/sec)
- Latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- LLM API calls (cost, latency, tokens)
- Database query time

---

### **Grafana (Dashboards)**

**Pre-Built Dashboards:**

1. **System Health:** CPU, memory, disk, network
2. **API Performance:** Request rate, latency, errors
3. **Business Metrics:** Goals created, coach queries, optimization runs
4. **Cost Tracking:** LLM spend, infrastructure costs

**Alert Rules:**

- API p95 latency >1 second
- Error rate >1%
- PostgreSQL connections >80% of max
- LLM cost >$100/day

---

### **Jaeger (Distributed Tracing)**

**Why Jaeger?**

- **Trace Requests:** Follow request flow (API → coach → LLM → DB)
- **Identify Bottlenecks:** Find slow components
- **Debug Errors:** See exact failure point in trace

**OpenTelemetry Integration:**

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

FastAPIInstrumentor.instrument_app(app)
```

---

### **Loki (Logging)**

**Why Loki?**

- **Grafana Integration:** Logs alongside metrics
- **Label-Based:** Query logs by tenant, user, endpoint
- **Cost-Effective:** No indexing overhead (like Elasticsearch)

**Log Format (Structured JSON):**

```json
{
  "timestamp": "2025-11-14T10:30:00Z",
  "level": "INFO",
  "tenant_id": "abc-123",
  "user_id": "user-456",
  "endpoint": "/coach/ask",
  "message": "Coach query processed",
  "latency_ms": 1850,
  "llm_provider": "local_llama3"
}
```

---

## 🚀 Deployment Architecture

### **Development: Docker Compose**

**Services:**

- PostgreSQL 16 (with extensions)
- Backend (FastAPI)
- Frontend (Next.js)
- Prometheus + Grafana + Loki + Jaeger
- Redis (caching)

**Start Command:**

```bash
docker-compose -f docker-compose.smb.yml up -d
```

---

### **Staging/Production: Single VM (Vertical Scaling)**

**For 1-5000 SMBs:**

- **Provider:** Hetzner, DigitalOcean, Linode (cost-effective)
- **Instance:** 16 vCPU, 64GB RAM, 500GB SSD
- **Cost:** ~$120-150/month

**Deployment:**

```bash
# Deploy backend + frontend + PostgreSQL
docker-compose -f docker-compose.production.yml up -d

# Set up backups (PostgreSQL → Backblaze B2)
pg_dump dyocense_db | b2 upload-file dyocense-backups backup-$(date +%Y%m%d).sql
```

---

### **Scale (>5000 SMBs): Kubernetes**

**When to Scale:**

- Single VM reaches CPU/memory limits
- Need multi-region deployment (latency optimization)
- Need high availability (99.99% uptime)

**Infrastructure:**

- **Kubernetes Cluster:** 3+ nodes (AWS EKS, GCP GKE, Azure AKS)
- **PostgreSQL:** Managed service (AWS RDS, GCP Cloud SQL) with read replicas
- **Redis:** Managed cluster (AWS ElastiCache, GCP Memorystore)
- **Load Balancer:** CloudFlare (DDoS protection, CDN)

**Cost:** ~$1500-3000/month (for 5000+ SMBs)

---

## ⚖️ Technology Trade-offs

### **Monolith vs. Microservices**

| Criteria | Monolith (v4.0) | Microservices (v1-3) | Winner |
|----------|----------------|---------------------|--------|
| **Ops Complexity** | Low (single deployment) | High (19 services) | ✅ Monolith |
| **Development Speed** | Fast (no cross-service changes) | Slow (coordinated releases) | ✅ Monolith |
| **Scalability** | Vertical (up to 5000 SMBs) | Horizontal (unlimited) | ⚖️ Tie (both work) |
| **Debugging** | Easy (single log stream) | Hard (distributed traces) | ✅ Monolith |
| **Cost** | <$1/tenant/mo | $5/tenant/mo | ✅ Monolith |

**Decision:** Start with monolith, migrate to microservices only if needed (>10,000 SMBs).

---

### **PostgreSQL vs. Specialized Databases**

| Workload | PostgreSQL Extension | Specialized DB | Cost Savings |
|----------|---------------------|----------------|--------------|
| **Time-Series** | TimescaleDB | InfluxDB | $200/mo |
| **Vector Search** | pgvector | Pinecone | $200/mo |
| **Graph Queries** | Apache AGE | Neo4j | $500/mo |
| **Full-Text Search** | Native (tsvector) | Elasticsearch | $300/mo |

**Decision:** Use PostgreSQL extensions until specialized DBs offer 10x better performance.

---

### **Local vs. Cloud LLMs**

| Metric | Local (Llama 3 8B) | Cloud (GPT-4o) | Winner |
|--------|-------------------|----------------|--------|
| **Cost** | $0.00/query | $0.05/query | ✅ Local |
| **Latency** | 300-500ms | 1-2 seconds | ✅ Local |
| **Accuracy** | 85% (good) | 95% (excellent) | ⚖️ Cloud |
| **Privacy** | 100% local | Data sent to OpenAI | ✅ Local |

**Decision:** Use hybrid approach (70% local, 30% cloud) for optimal cost/quality balance.

---

## 🎯 Conclusion

### **Key Architectural Bets**

1. **PostgreSQL as Single Source of Truth**
   - ✅ Simplifies operations (one DB to manage)
   - ✅ ACID guarantees for critical business data
   - ✅ Portable across clouds (no lock-in)

2. **Hybrid AI Architecture (LLMs + Optimization + Forecasting)**
   - ✅ Mathematically rigorous (patentable IP)
   - ✅ Not just "ChatGPT wrapper" (unique value)
   - ✅ Cost-effective (80% savings vs. cloud-only)

3. **Open-Source First**
   - ✅ No vendor lock-in (own the stack)
   - ✅ Community-driven innovation (battle-tested tools)
   - ✅ Cost predictability (no surprise bills)

4. **Monolith Over Microservices**
   - ✅ Faster development (single codebase)
   - ✅ Lower ops overhead (80% reduction)
   - ✅ Better for SMB scale (0-10,000 tenants)

### **Next Steps**

1. **Review [Implementation Roadmap](./Implementation-Roadmap.md)** for 12-week execution plan
2. **Set up local development** (follow [00-READ-ME-FIRST.md](./00-READ-ME-FIRST.md))
3. **Start Phase 0** (PostgreSQL migration, monolith structure)

**Let's build! 🚀**
