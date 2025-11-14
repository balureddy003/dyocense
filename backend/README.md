# Dyocense v4.0 Backend - Developer Guide

**Unified FastAPI Monolith** replacing 19 microservices

---

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 16+ with extensions (use Docker Compose)
- Redis (optional, for caching)

### 2. Setup

```bash
# Clone repository
git clone <repo-url>
cd dyocense

# Install dependencies
make setup

# Start external services (PostgreSQL, Prometheus, Grafana, etc.)
docker-compose -f docker-compose.external.yml --profile monitoring up -d

# Run database migrations
make migrate

# Start backend server
make dev
```

Backend will be available at **<http://localhost:8001>**

- API Docs: <http://localhost:8001/docs>
- Health Check: <http://localhost:8001/api/health>
- Metrics: <http://localhost:8001/metrics>

---

## 📁 Project Structure

```
dyocense/
├── backend/                    # v4.0 Unified Backend (NEW)
│   ├── main.py                # FastAPI app entry point
│   ├── config.py              # Pydantic settings
│   ├── dependencies.py        # Dependency injection
│   ├── models/                # SQLAlchemy models
│   │   └── __init__.py       # Database schema
│   ├── routes/                # API endpoints
│   │   ├── health.py         # Health checks
│   │   ├── tenant.py         # Tenant management
│   │   ├── coach.py          # AI coach
│   │   ├── optimizer.py      # Optimization
│   │   ├── forecaster.py     # Forecasting
│   │   ├── evidence.py       # Causal inference
│   │   └── connector.py      # Data connectors
│   ├── services/              # Business logic
│   │   ├── coach/            # AI coach service
│   │   ├── optimizer/        # Optimization engine
│   │   ├── forecaster/       # Forecasting service
│   │   ├── evidence/         # Causal inference
│   │   └── connectors/       # Data ingestion
│   ├── agents/                # LangGraph agents
│   ├── schemas/               # Pydantic schemas
│   └── utils/                 # Helpers
│       ├── logging.py        # Structured logging
│       └── observability.py  # Tracing & metrics
├── services/                   # Legacy microservices (for reference)
├── infra/                      # Infrastructure configs
│   ├── postgres/              # PostgreSQL configs
│   ├── prometheus/            # Metrics collection
│   ├── grafana/               # Dashboards
│   ├── loki/                  # Log aggregation
│   └── nginx/                 # Reverse proxy
├── alembic/                    # Database migrations
├── tests/                      # Test suite
├── .env                        # Environment variables
├── Makefile                    # Development commands
└── requirements-v4.txt         # Python dependencies
```

---

## 🔧 Configuration

### Environment Variables

Copy `.env.external.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://dyocense:password@localhost:5432/dyocense

# Redis (optional)
REDIS_URL=redis://:password@localhost:6379/0

# LLM
ENABLE_LOCAL_LLM=true
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama3:8b
OPENAI_API_KEY=sk-...

# Observability
ENABLE_PROMETHEUS=true
ENABLE_TRACING=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:8001
```

See `backend/config.py` for all available settings.

---

## 🗄️ Database

### Schema

- **Tenants** - Multi-tenant isolation
- **Users** - SMB employees
- **SmartGoals** - Goal tracking
- **BusinessMetrics** - Time-series KPIs (TimescaleDB)
- **CoachingSessions** - AI chat history with embeddings (pgvector)
- **DataSources** - External integrations
- **EvidenceGraph** - Causal relationships
- **Forecasts** - Predictions
- **OptimizationRuns** - Optimization results
- **ExternalBenchmarks** - Industry data

### Migrations

```bash
# Create new migration
make migrate-create

# Apply migrations
make migrate

# Rollback
make migrate-rollback

# Connect to database
make db-shell
```

### Row-Level Security (RLS)

All tenant-scoped tables use PostgreSQL RLS for data isolation:

```python
# Automatically filtered by tenant_id
async def get_metrics(db: AsyncSession = Depends(set_tenant_context)):
    result = await db.execute(select(BusinessMetric))
    return result.scalars().all()  # Only current tenant's metrics
```

---

## 🎯 Development Workflow

### 1. Add New Feature

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Add route in backend/routes/
# backend/routes/my_feature.py

# 3. Add service logic in backend/services/
# backend/services/my_feature/service.py

# 4. Update backend/routes/__init__.py to export router

# 5. Add tests
# tests/test_my_feature.py

# 6. Run tests
make test

# 7. Start dev server
make dev

# 8. Test in browser
open http://localhost:8001/docs
```

### 2. Database Changes

```bash
# 1. Modify backend/models/__init__.py

# 2. Generate migration
make migrate-create
# Enter migration name when prompted

# 3. Review migration in alembic/versions/

# 4. Apply migration
make migrate

# 5. Verify in database
make db-shell
\d+ table_name
```

### 3. Testing

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_my_feature.py -v

# Run with coverage
pytest --cov=backend tests/

# Load testing
locust -f tests/load/locustfile.py
```

---

## 📊 Observability

### Metrics (Prometheus)

Access metrics at <http://localhost:9090>

Key metrics:

- `http_requests_total` - Request count by endpoint
- `http_request_duration_seconds` - Latency
- `llm_requests_total` - LLM calls (local vs cloud)
- `llm_cost_dollars` - Cumulative LLM costs
- `db_query_duration_seconds` - Database performance

### Dashboards (Grafana)

Access dashboards at <http://localhost:3000> (admin/admin)

Pre-configured dashboards:

- System health (CPU, memory, disk)
- API performance
- Database metrics
- LLM usage and costs

### Tracing (Jaeger)

Access traces at <http://localhost:16686>

Distributed tracing across:

- HTTP requests
- Database queries
- LLM API calls
- External API calls

### Logs (Loki)

Structured JSON logs automatically shipped to Loki.

Query logs in Grafana Explore:

```
{service="dyocense-backend"} |= "error"
```

---

## 🤖 AI Coach

### LLM Routing

Hybrid routing saves 80% on LLM costs:

- **70% local** (Llama 3 8B via Ollama)
- **30% cloud** (GPT-4o for complex queries)

Routing logic in `backend/services/coach/llm_router.py`

### Agents (LangGraph)

- **goal_planner** - Decompose user goals into SMART goals
- **evidence_analyzer** - Root cause analysis
- **forecaster** - Predict future metrics
- **optimizer** - Recommend optimal actions

---

## 🔐 Security

### Authentication

JWT-based authentication:

```python
from backend.dependencies import CurrentUser

@router.get("/protected")
async def protected_route(user: CurrentUser):
    return {"user_id": user["user_id"]}
```

### Row-Level Security (RLS)

PostgreSQL RLS ensures tenant isolation:

```sql
CREATE POLICY tenant_isolation ON business_metrics
USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

Set tenant context automatically:

```python
from backend.dependencies import set_tenant_context

@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(set_tenant_context)):
    # RLS automatically filters by tenant
    ...
```

---

## 🚢 Deployment

### Development

```bash
make dev
```

### Production

```bash
# Build Docker image
docker build -f Dockerfile.unified -t dyocense:latest .

# Run with docker-compose
docker-compose -f docker-compose.external.yml --profile production up -d

# Or run standalone
docker run -p 8001:8001 \
  -e DATABASE_URL=... \
  -e OPENAI_API_KEY=... \
  dyocense:latest
```

---

## 📚 API Documentation

### Auto-generated Docs

- **Swagger UI**: <http://localhost:8001/docs>
- **ReDoc**: <http://localhost:8001/redoc>

### Example Requests

**Health Check**

```bash
curl http://localhost:8001/api/health
```

**Create Tenant**

```bash
curl -X POST http://localhost:8001/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "owner_email": "owner@acme.com"}'
```

**AI Coach Chat**

```bash
curl -X POST http://localhost:8001/api/v1/coach/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "How can I increase revenue?"}'
```

---

## 🐛 Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.external.yml ps postgres

# Check connection
psql postgresql://dyocense:dyocense@localhost:5432/dyocense

# View logs
docker-compose -f docker-compose.external.yml logs postgres
```

### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=.

# Or use make commands which set it automatically
make dev
```

### Migration Errors

```bash
# Reset database (WARNING: deletes all data)
docker-compose -f docker-compose.external.yml down -v
docker-compose -f docker-compose.external.yml up -d postgres
make migrate
```

---

## 📖 References

- **FastAPI**: <https://fastapi.tiangolo.com/>
- **SQLAlchemy**: <https://docs.sqlalchemy.org/>
- **Alembic**: <https://alembic.sqlalchemy.org/>
- **TimescaleDB**: <https://docs.timescale.com/>
- **pgvector**: <https://github.com/pgvector/pgvector>
- **LangGraph**: <https://langchain-ai.github.io/langgraph/>
- **Prometheus**: <https://prometheus.io/docs/>

---

## 🎓 Learning Path

1. **Day 1**: Setup environment, run `make dev`, explore API docs
2. **Day 2**: Understand database schema in `backend/models/__init__.py`
3. **Day 3**: Study route handlers in `backend/routes/`
4. **Day 4**: Explore dependency injection in `backend/dependencies.py`
5. **Day 5**: Build a simple feature end-to-end

---

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Add tests
4. Run `make test`
5. Submit pull request

---

**Questions?** Check `/docs` folder for architecture documentation.
