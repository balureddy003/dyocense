# Services

This directory contains service modules that are mounted in the **unified kernel** (v4.0 monolith architecture). Services are no longer deployed as separate microservices but are loaded as FastAPI sub-apps within a single kernel process.

## Architecture (v4.0)

**Deployment Model:** Monolith with service modules mounted via `services/kernel/main.py`

**Database:** PostgreSQL with extensions (pgvector, TimescaleDB, pg_cron, Apache AGE)

**Single Entry Point:** All services exposed through unified kernel at `http://localhost:8001`

## Active Services (Mounted in Kernel)

These services are loaded and mounted in the unified kernel:

- **`accounts/`** - Multi-tenant account management, authentication, API tokens
- **`analyze/`** - Data analysis and CSV insights
- **`chat/`** - Chat interface and conversation management
- **`compiler/`** - OPS compiler for business operations
- **`connectors/`** - Data source connectors (feature-flagged)
- **`diagnostician/`** - Diagnostics and troubleshooting
- **`evidence/`** - Evidence tracking and audit trail
- **`explainer/`** - Explanation generation for decisions
- **`forecast/`** - Demand forecasting and time-series prediction
- **`marketplace/`** - Template and playbook marketplace
- **`optimiser/`** - Optimization algorithms (OR-Tools, PuLP)
- **`orchestrator/`** - Multi-agent orchestration
- **`plan/`** - Planning and scheduling
- **`policy/`** - Policy evaluation (OPA/Rego simulation)
- **`smb_gateway/`** - Primary SMB API (goals, tasks, coach, reports)
- **`kernel/`** - Unified kernel that mounts all services

## Running the Unified Kernel

```bash
# Using Docker Compose (recommended)
docker-compose -f docker-compose.smb.yml up kernel

# Or run directly
cd /Users/balu/Projects/dyocense
source .venv/bin/activate
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001
```

**Health Check:**

```bash
curl http://localhost:8001/health
curl http://localhost:8001/health/detailed
```

**API Documentation:**

```bash
open http://localhost:8001/docs
```

## Service Mounting Pattern

Services are dynamically loaded in `services/kernel/main.py`:

```python
# Load service as FastAPI sub-app
chat_app = _load_service("services.chat.main")

# Mount at /api/{service}
app.mount("/api/chat", chat_app)
```

**SMB Gateway** is mounted directly at root level to expose `/v1/tenants/*` endpoints without prefix.

## Development

### Adding a New Service

1. Create service directory: `services/my_service/`
2. Create FastAPI app: `services/my_service/main.py`
3. Add to kernel loader in `services/kernel/main.py`
4. Test via unified kernel endpoint

### Dependencies

All service dependencies are consolidated in root-level `requirements-v4.txt`:

```bash
pip install -r requirements-v4.txt
```

**No per-service requirements.txt files** - everything is in the monolith.

### Database Access

All services use **PostgreSQL only**:

- Connection via `packages.kernel_common.persistence`
- Multi-tenancy via Row-Level Security (RLS)
- Vector search via pgvector
- Time-series via TimescaleDB (optional)

## Deprecated Services

The following services have been **removed** in v4.0:

- ~~`agent_shell/`~~ - Demo service
- ~~`keystone_proxy/`~~ - Proxy service (deprecated)
- ~~`notifications/`~~ - Not used
- ~~`scenario/`~~ - Replaced by orchestrator

## Migration from v3.0

See `/docs/Refactoring-Guide.md` and `/docs/PHASE0-IMPLEMENTATION.md` for complete migration guide.

**Key Changes:**

- 19 microservices → 1 monolith
- 4 databases → 1 PostgreSQL
- HTTP inter-service calls → Direct Python imports
- Separate deployments → Single kernel deployment
- $1,150/mo infrastructure → $50/mo
