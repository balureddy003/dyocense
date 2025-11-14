# 🔧 Refactoring Guide: v3.0 → v4.0

**Version:** 4.0 (Microservices to Monolith)  
**Last Updated:** November 14, 2025  
**Status:** Phase 0 Planning

---

## 📋 Table of Contents

1. [Overview](#1-overview)
2. [Current State Assessment](#2-current-state-assessment)
3. [Phase 0: Foundation Refactoring](#3-phase-0-foundation-refactoring)
4. [Migration Strategy](#4-migration-strategy)
5. [Code Consolidation](#5-code-consolidation)
6. [Database Migration](#6-database-migration)
7. [Testing Strategy](#7-testing-strategy)
8. [Rollback Plan](#8-rollback-plan)

---

## 🎯 1. Overview

### **Refactoring Objectives**

> **"Simplify architecture without losing functionality"**

**Primary Goals:**

- ✅ **Consolidate Services:** 19 microservices → 1 FastAPI monolith
- ✅ **Unify Databases:** 4 databases → 1 PostgreSQL with extensions
- ✅ **Reduce Complexity:** 80% reduction in operational overhead
- ✅ **Cut Costs:** $5/tenant → <$1/tenant/month
- ✅ **Maintain Features:** Zero feature regression during migration

---

### **Why Refactor?**

| Problem (v3.0) | Solution (v4.0) | Impact |
|----------------|-----------------|--------|
| **19 microservices** | 1 monolith | 80% less ops overhead |
| **4 databases** | 1 PostgreSQL | $1200/mo savings |
| **Complex deployments** | Docker Compose | Faster deploys |
| **High cloud costs** | Local LLMs | 80% LLM cost reduction |
| **Network latency** | In-process calls | 10x faster |

---

## 📊 2. Current State Assessment

### **Current Architecture Inventory**

**Services (19 total):**

```
services/
├── accounts/          # User management
├── agent_shell/       # Multi-agent orchestrator
├── analyze/           # Analytics service
├── chat/              # Conversational interface
├── compiler/          # Goal compiler
├── connectors/        # Data ingestion
├── diagnostician/     # Root cause analysis
├── evidence/          # Causal inference
├── explainer/         # Explanation generator
├── forecast/          # Time-series forecasting
├── kernel/            # Core business logic
├── knowledge/         # RAG/embeddings
├── observe/           # Observability
├── optimize/          # Optimization solver
├── plan/              # Goal planning
├── playbooks/         # Workflow templates
├── reporter/          # Report generation
├── trust/             # Security/auth
└── versioning/        # Version control
```

---

**Databases (4 total):**

| Database | Purpose | Cost/Month | Replacement |
|----------|---------|------------|-------------|
| **PostgreSQL** | Primary data | $50 | ✅ Keep + extend |
| **MongoDB** | Document store | $200 | ❌ Migrate to JSONB |
| **InfluxDB** | Time-series | $200 | ❌ Use TimescaleDB |
| **Pinecone** | Vector search | $200 | ❌ Use pgvector |
| **Neo4j** | Graph queries | $500 | ❌ Use Apache AGE |

**Total DB Cost:** $1150/mo → **$50/mo** (98% reduction)

---

### **Code Metrics**

```bash
# Current codebase analysis
cloc services/

Language          files       blank     comment        code
---------------------------------------------------------
Python             450        8500       4200         35000
TypeScript         120        2500       1200         12000
YAML                85        1200        500          3500
SQL                 45         800        600          2800
Dockerfile          25         150         50           400
---------------------------------------------------------
TOTAL              725       13150       6550         53700
```

**Estimated Reduction:** 40% code deletion (consolidating duplicates, removing service boilerplate)

---

## 🏗️ 3. Phase 0: Foundation Refactoring

### **Week 1-2: Database Consolidation**

**Step 1: PostgreSQL Extension Setup**

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Verify installation
SELECT extname, extversion FROM pg_extension 
WHERE extname IN ('timescaledb', 'vector', 'age', 'pg_cron');
```

---

**Step 2: Migrate MongoDB Collections to PostgreSQL JSONB**

```python
# scripts/migrate_mongo_to_postgres.py
import pymongo
from sqlalchemy import create_engine, text

# Source: MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["dyocense"]

# Target: PostgreSQL
pg_engine = create_engine("postgresql://user:pass@localhost:5432/dyocense")

# Collections to migrate
collections = [
    "goals",
    "tasks", 
    "conversations",
    "connector_configs"
]

for collection_name in collections:
    print(f"Migrating {collection_name}...")
    
    # Read from MongoDB
    mongo_collection = mongo_db[collection_name]
    documents = list(mongo_collection.find({}))
    
    # Write to PostgreSQL
    with pg_engine.connect() as conn:
        for doc in documents:
            # Convert MongoDB _id to UUID
            doc_id = str(doc["_id"])
            doc.pop("_id")
            
            # Insert as JSONB
            conn.execute(text(f"""
                INSERT INTO {collection_name} (id, tenant_id, data, created_at)
                VALUES (:id, :tenant_id, :data::jsonb, :created_at)
                ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data
            """), {
                "id": doc_id,
                "tenant_id": doc.get("tenant_id"),
                "data": json.dumps(doc),
                "created_at": doc.get("created_at")
            })
        
        conn.commit()
    
    print(f"✅ Migrated {len(documents)} documents from {collection_name}")
```

---

**Step 3: Migrate InfluxDB Metrics to TimescaleDB**

```python
# scripts/migrate_influx_to_timescale.py
from influxdb_client import InfluxDBClient
from sqlalchemy import create_engine, text

# Source: InfluxDB
influx_client = InfluxDBClient(url="http://localhost:8086", token="...", org="dyocense")
query_api = influx_client.query_api()

# Target: PostgreSQL + TimescaleDB
pg_engine = create_engine("postgresql://user:pass@localhost:5432/dyocense")

# Create hypertable
with pg_engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS metrics (
            time TIMESTAMPTZ NOT NULL,
            tenant_id UUID NOT NULL,
            metric_type TEXT NOT NULL,
            metric_value NUMERIC NOT NULL,
            tags JSONB
        );
        
        SELECT create_hypertable('metrics', 'time', if_not_exists => TRUE);
    """))
    conn.commit()

# Migrate data
query = '''
from(bucket: "dyocense")
  |> range(start: -90d)
  |> filter(fn: (r) => r._measurement == "business_metrics")
'''

tables = query_api.query(query)

with pg_engine.connect() as conn:
    for table in tables:
        for record in table.records:
            conn.execute(text("""
                INSERT INTO metrics (time, tenant_id, metric_type, metric_value, tags)
                VALUES (:time, :tenant_id, :metric_type, :value, :tags::jsonb)
            """), {
                "time": record.get_time(),
                "tenant_id": record.values.get("tenant_id"),
                "metric_type": record.get_field(),
                "value": record.get_value(),
                "tags": json.dumps(record.values)
            })
    conn.commit()

print("✅ Migrated InfluxDB metrics to TimescaleDB")
```

---

**Step 4: Migrate Pinecone Vectors to pgvector**

```python
# scripts/migrate_pinecone_to_pgvector.py
import pinecone
from sqlalchemy import create_engine, text

# Source: Pinecone
pinecone.init(api_key="...", environment="us-west1-gcp")
index = pinecone.Index("dyocense-embeddings")

# Target: PostgreSQL + pgvector
pg_engine = create_engine("postgresql://user:pass@localhost:5432/dyocense")

# Create vector table
with pg_engine.connect() as conn:
    conn.execute(text("""
        CREATE EXTENSION IF NOT EXISTS vector;
        
        CREATE TABLE IF NOT EXISTS embeddings (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536),  -- OpenAI embedding dimension
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """))
    conn.commit()

# Fetch all vectors from Pinecone
fetch_response = index.fetch(ids=index.describe_index_stats()["namespaces"][""]["vectors"])

with pg_engine.connect() as conn:
    for vector_id, vector_data in fetch_response["vectors"].items():
        conn.execute(text("""
            INSERT INTO embeddings (id, tenant_id, content, embedding, metadata)
            VALUES (:id, :tenant_id, :content, :embedding::vector, :metadata::jsonb)
            ON CONFLICT (id) DO UPDATE SET embedding = EXCLUDED.embedding
        """), {
            "id": vector_id,
            "tenant_id": vector_data["metadata"]["tenant_id"],
            "content": vector_data["metadata"]["content"],
            "embedding": vector_data["values"],
            "metadata": json.dumps(vector_data["metadata"])
        })
    conn.commit()

print("✅ Migrated Pinecone vectors to pgvector")
```

---

### **Week 3-4: Service Consolidation**

**Step 1: Create Monolith Structure**

```bash
# New directory structure
mkdir -p dyocense_monolith/{api,services,models,utils}

dyocense_monolith/
├── api/
│   ├── __init__.py
│   ├── auth.py          # Authentication endpoints
│   ├── goals.py         # Goal management
│   ├── chat.py          # Coach chat interface
│   ├── metrics.py       # Metrics API
│   └── connectors.py    # Data connectors
├── services/
│   ├── __init__.py
│   ├── coach_service.py      # Multi-agent coach
│   ├── goal_service.py       # Goal planning
│   ├── optimizer_service.py  # Optimization
│   ├── forecaster_service.py # Forecasting
│   ├── evidence_service.py   # Causal analysis
│   ├── connector_service.py  # Data ingestion
│   └── analytics_service.py  # Reporting
├── models/
│   ├── __init__.py
│   ├── base.py          # SQLAlchemy base
│   ├── tenant.py        # Tenant model
│   ├── user.py          # User model
│   ├── goal.py          # Goal model
│   └── metric.py        # Metric model
├── utils/
│   ├── __init__.py
│   ├── auth.py          # JWT helpers
│   ├── logger.py        # Structured logging
│   └── config.py        # Configuration
├── main.py              # FastAPI app entry
└── requirements.txt     # Python dependencies
```

---

**Step 2: Consolidate Service Code**

```python
# dyocense_monolith/services/coach_service.py
"""
Consolidated Coach Service
Combines: agent_shell, chat, explainer, compiler
"""
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from .goal_service import GoalService
from .forecaster_service import ForecasterService
from .optimizer_service import OptimizerService
from .evidence_service import EvidenceService

class CoachService:
    def __init__(self, db_session):
        self.db = db_session
        self.goal_service = GoalService(db_session)
        self.forecaster = ForecasterService(db_session)
        self.optimizer = OptimizerService(db_session)
        self.evidence = EvidenceService(db_session)
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Create multi-agent state machine"""
        workflow = StateGraph(CoachState)
        
        # Add agent nodes
        workflow.add_node("retrieve", self._retrieve_context)
        workflow.add_node("goal_planner", self._plan_goal)
        workflow.add_node("forecaster", self._forecast)
        workflow.add_node("optimizer", self._optimize)
        workflow.add_node("evidence", self._analyze_evidence)
        workflow.add_node("respond", self._generate_response)
        
        # Define flow
        workflow.set_entry_point("retrieve")
        workflow.add_conditional_edges("retrieve", self._route_to_agent)
        workflow.add_edge("goal_planner", "respond")
        workflow.add_edge("forecaster", "respond")
        workflow.add_edge("optimizer", "respond")
        workflow.add_edge("evidence", "respond")
        workflow.add_edge("respond", END)
        
        return workflow.compile()
    
    async def ask(self, query: str, tenant_id: str) -> dict:
        """Main coach interface"""
        initial_state = {
            "user_query": query,
            "tenant_id": tenant_id,
            "conversation_history": []
        }
        
        result = await self.workflow.ainvoke(initial_state)
        return result["final_response"]
```

---

**Step 3: Create Unified FastAPI App**

```python
# dyocense_monolith/main.py
"""
Dyocense v4.0 - Unified FastAPI Application
Consolidates all microservices into single monolith
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from prometheus_client import make_asgi_app

from .api import auth, goals, chat, metrics, connectors
from .utils.config import settings
from .utils.logger import StructuredLogger
from .models.base import engine, SessionLocal

# Initialize app
app = FastAPI(
    title="Dyocense AI Coach",
    version="4.0.0",
    description="Cost-optimized AI business coach for SMBs"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Structured logging
logger = StructuredLogger("dyocense-api")

# Dependency: DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Middleware: Tenant context for RLS
@app.middleware("http")
async def set_tenant_context(request: Request, call_next):
    if request.url.path not in ["/health", "/metrics", "/docs"]:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            payload = decode_jwt(token)
            tenant_id = payload.get("tenant_id")
            
            # Set PostgreSQL session variable for RLS
            request.state.tenant_id = tenant_id
    
    response = await call_next(request)
    return response

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(goals.router, prefix="/goals", tags=["goals"])
app.include_router(chat.router, prefix="/chat", tags=["coach"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(connectors.router, prefix="/connectors", tags=["connectors"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "4.0.0"}

# Startup event
@app.on_event("startup")
async def startup():
    logger.log("INFO", "Dyocense v4.0 starting...")
    # Initialize DB connection pool
    # Load ML models (if any)
    logger.log("INFO", "Startup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
```

---

## 🔄 4. Migration Strategy

### **Phased Rollout**

**Phase 0.1: Database Migration (Week 1-2)**

- ✅ Set up PostgreSQL extensions
- ✅ Migrate MongoDB → JSONB
- ✅ Migrate InfluxDB → TimescaleDB
- ✅ Migrate Pinecone → pgvector
- ✅ Test data integrity (100% accuracy required)

**Phase 0.2: Code Consolidation (Week 3-4)**

- ✅ Create monolith structure
- ✅ Consolidate service logic
- ✅ Build unified API layer
- ✅ Write integration tests

**Phase 0.3: Parallel Deployment (Week 5-6)**

- ✅ Deploy monolith alongside microservices
- ✅ Route 10% traffic to monolith
- ✅ Monitor error rates, latency
- ✅ Gradually increase to 100%

**Phase 0.4: Decommission (Week 7-8)**

- ✅ Shut down microservices
- ✅ Delete old databases (after backup)
- ✅ Update documentation
- ✅ Celebrate cost savings! 🎉

---

### **Traffic Routing Strategy**

```nginx
# nginx.conf - Canary deployment
upstream microservices {
    server microservices:8000 weight=90;
}

upstream monolith {
    server monolith:8000 weight=10;  # Start with 10% traffic
}

server {
    listen 80;
    server_name api.dyocense.com;
    
    location / {
        proxy_pass http://monolith;  # Gradually shift traffic
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📦 5. Code Consolidation

### **Service Mapping**

| Old Microservice | New Module | Lines of Code | Reduction |
|------------------|------------|---------------|-----------|
| `accounts/` | `services/auth_service.py` | 1200 → 800 | 33% |
| `agent_shell/` + `chat/` | `services/coach_service.py` | 2500 → 1500 | 40% |
| `compiler/` + `plan/` | `services/goal_service.py` | 1800 → 1200 | 33% |
| `forecast/` | `services/forecaster_service.py` | 1000 → 800 | 20% |
| `optimize/` | `services/optimizer_service.py` | 1500 → 1200 | 20% |
| `evidence/` + `diagnostician/` | `services/evidence_service.py` | 1700 → 1200 | 29% |
| `connectors/` | `services/connector_service.py` | 2000 → 1500 | 25% |
| `analyze/` + `reporter/` | `services/analytics_service.py` | 1600 → 1200 | 25% |

**Total Reduction:** ~35% less code (removing service boilerplate, API clients, duplicate logic)

---

### **Dependency Reduction**

**Before (v3.0):**

```txt
# requirements.txt (per service)
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
requests==2.31.0        # For inter-service calls
pymongo==4.6.0
influxdb-client==1.38.0
pinecone-client==2.2.4
neo4j==5.14.0
# ... 50+ dependencies per service
```

**After (v4.0):**

```txt
# requirements.txt (monolith)
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
# NO inter-service HTTP clients!
psycopg2-binary==2.9.9  # PostgreSQL only
langgraph==0.0.25
langchain-openai==0.0.5
ortools==9.8.3296
prophet==1.1.5
dowhy==0.11.1
prometheus-client==0.19.0
# ... ~30 dependencies total
```

---

## 🗄️ 6. Database Migration

### **Schema Comparison**

**Before (v3.0):**

```
PostgreSQL (primary):
  - tenants
  - users
  - goals
  
MongoDB:
  - tasks
  - conversations
  - connector_configs
  
InfluxDB:
  - business_metrics (time-series)
  
Pinecone:
  - embeddings (vectors)
  
Neo4j:
  - causal_graph (relationships)
```

**After (v4.0):**

```
PostgreSQL (all-in-one):
  - tenants
  - users
  - goals
  - tasks (JSONB)
  - conversations (JSONB)
  - connectors (JSONB)
  - metrics (TimescaleDB hypertable)
  - embeddings (pgvector)
  - causal_graph (Apache AGE)
```

---

### **Data Integrity Validation**

```python
# scripts/validate_migration.py
"""
Validate data migrated correctly from old DBs to PostgreSQL
"""

def validate_mongodb_migration():
    """Compare MongoDB count with PostgreSQL JSONB count"""
    mongo_count = mongo_db.goals.count_documents({})
    pg_count = pg_engine.execute("SELECT COUNT(*) FROM goals").scalar()
    
    assert mongo_count == pg_count, f"Mismatch: Mongo={mongo_count}, PG={pg_count}"
    print(f"✅ MongoDB migration: {pg_count} goals")

def validate_influxdb_migration():
    """Compare metric counts"""
    influx_query = 'from(bucket: "dyocense") |> range(start: -90d) |> count()'
    influx_count = len(query_api.query(influx_query))
    
    pg_count = pg_engine.execute("SELECT COUNT(*) FROM metrics WHERE time > NOW() - INTERVAL '90 days'").scalar()
    
    assert influx_count == pg_count, f"Mismatch: Influx={influx_count}, PG={pg_count}"
    print(f"✅ InfluxDB migration: {pg_count} metrics")

def validate_pinecone_migration():
    """Compare vector counts"""
    pinecone_stats = index.describe_index_stats()
    pinecone_count = pinecone_stats["total_vector_count"]
    
    pg_count = pg_engine.execute("SELECT COUNT(*) FROM embeddings").scalar()
    
    assert pinecone_count == pg_count, f"Mismatch: Pinecone={pinecone_count}, PG={pg_count}"
    print(f"✅ Pinecone migration: {pg_count} vectors")

# Run all validations
validate_mongodb_migration()
validate_influxdb_migration()
validate_pinecone_migration()

print("🎉 All data migrations validated successfully!")
```

---

## 🧪 7. Testing Strategy

### **Test Coverage Requirements**

| Test Type | Coverage Target | Priority |
|-----------|----------------|----------|
| **Unit Tests** | 80%+ | High |
| **Integration Tests** | 60%+ | High |
| **E2E Tests** | Critical paths | Medium |
| **Load Tests** | 100 req/s | Medium |
| **Migration Tests** | 100% data accuracy | **Critical** |

---

### **Integration Test Example**

```python
# tests/test_coach_service_integration.py
import pytest
from fastapi.testclient import TestClient
from dyocense_monolith.main import app

client = TestClient(app)

@pytest.fixture
def test_tenant():
    # Create test tenant
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "company_name": "Test Corp"
    })
    return response.json()

def test_coach_ask_goal_generation(test_tenant):
    """Test coach can generate SMART goal"""
    
    # Login
    login = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "testpass123"
    })
    token = login.json()["access_token"]
    
    # Ask coach
    response = client.post(
        "/chat/ask",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "I want to increase revenue by 20% next quarter"}
    )
    
    assert response.status_code == 200
    result = response.json()
    
    # Verify SMART goal generated
    assert "goal" in result
    assert result["goal"]["specific"] is not None
    assert result["goal"]["measurable"] is not None
    assert result["goal"]["target_value"] == 0.20  # 20% increase

def test_data_isolation_rls(test_tenant):
    """Test Row-Level Security prevents cross-tenant access"""
    
    # Create two tenants
    tenant_a = create_test_tenant("tenant_a@example.com")
    tenant_b = create_test_tenant("tenant_b@example.com")
    
    # Tenant A creates goal
    goal_a = client.post(
        "/goals",
        headers={"Authorization": f"Bearer {tenant_a['token']}"},
        json={"description": "Revenue goal"}
    )
    
    # Tenant B tries to access Tenant A's goal
    response = client.get(
        f"/goals/{goal_a.json()['goal_id']}",
        headers={"Authorization": f"Bearer {tenant_b['token']}"}
    )
    
    # Should get 404 (not 403, to prevent leaking existence)
    assert response.status_code == 404
```

---

### **Load Testing**

```python
# tests/load_test.py
from locust import HttpUser, task, between

class DyocenseUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "testpass123"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def ask_coach(self):
        self.client.post(
            "/chat/ask",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"query": "How can I reduce costs?"}
        )
    
    @task(2)
    def get_metrics(self):
        self.client.get(
            "/metrics?metric_type=revenue&days=30",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def create_goal(self):
        self.client.post(
            "/goals",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"description": "Increase revenue"}
        )

# Run: locust -f tests/load_test.py --host=http://localhost:8000
# Target: 100 concurrent users, <500ms P95 latency
```

---

## 🔙 8. Rollback Plan

### **Rollback Triggers**

**Automatic Rollback if:**

- ❌ Error rate > 1% for 5 minutes
- ❌ P95 latency > 2 seconds
- ❌ Database connection failures
- ❌ Data corruption detected

**Manual Rollback if:**

- 🔴 Critical bug discovered
- 🔴 Performance degradation
- 🔴 Customer complaints spike

---

### **Rollback Procedure**

```bash
#!/bin/bash
# scripts/rollback_to_microservices.sh

echo "🚨 Initiating rollback to v3.0 microservices..."

# Step 1: Reroute traffic to old microservices
kubectl set image deployment/api-gateway \
    nginx=nginx:v3.0 --record

# Step 2: Scale down monolith
kubectl scale deployment/dyocense-monolith --replicas=0

# Step 3: Scale up microservices
kubectl scale deployment/agent-shell --replicas=3
kubectl scale deployment/chat-service --replicas=3
kubectl scale deployment/forecast-service --replicas=2
# ... (scale all 19 services)

# Step 4: Restore old databases (from hourly backups)
pg_restore -d dyocense_v3 /backups/postgres_latest.dump
mongorestore --db dyocense /backups/mongo_latest/

# Step 5: Verify health
curl http://api.dyocense.com/health

echo "✅ Rollback complete. Monitoring for stability..."
```

---

### **Data Backup Strategy**

```bash
# Automated backups during migration (hourly)
SELECT cron.schedule(
    'backup-during-migration',
    '0 * * * *',  -- Every hour
    $$
    COPY (SELECT * FROM goals) TO '/backups/goals_$(date +%Y%m%d_%H%M%S).csv' CSV HEADER;
    COPY (SELECT * FROM metrics) TO '/backups/metrics_$(date +%Y%m%d_%H%M%S).csv' CSV HEADER;
    $$
);

# pgBackRest continuous archiving
pgbackrest --stanza=dyocense --type=full backup
```

---

## 📈 Success Metrics

### **Phase 0 Completion Criteria**

**Technical Metrics:**

- ✅ All 4 databases consolidated to PostgreSQL
- ✅ All 19 services consolidated to 1 monolith
- ✅ 100% test coverage on critical paths
- ✅ P95 latency < 500ms
- ✅ Error rate < 0.1%
- ✅ Zero data loss during migration

**Business Metrics:**

- ✅ Infrastructure cost reduced from $1200/mo → $50/mo
- ✅ Deployment time reduced from 2 hours → 10 minutes
- ✅ Onboarding new developers: 2 weeks → 3 days
- ✅ Zero customer-facing incidents during migration

---

## 🎯 Next Steps

1. **Review [Implementation Roadmap](./Implementation-Roadmap.md)** for Phase 1-2 timeline
2. **Review [Technology Stack Selection](./Technology Stack Selection.md)** for architecture rationale
3. **Start Week 1** of Phase 0 (Database Migration)

---

## 📚 References

- [Design Document](./Design-Document.md) - v4.0 architecture overview
- [Data Architecture](./Data-Architecture.md) - PostgreSQL schema design
- [Service Architecture](./Service-Architecture.md) - Modular monolith structure
- [Security & Multi-Tenancy](./Security & Multi-Tenancy.md) - RLS implementation

---

**Ready to refactor! Let's build v4.0! 🚀**
