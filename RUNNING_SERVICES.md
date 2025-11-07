# Running Dyocense Services After Refactor

This guide shows how to run the Dyocense services after the kernel consolidation and planner integration.

## 🎯 Quick Start (Recommended)

### Option 1: Unified Kernel (Single Process)

The **recommended** way to run all services:

```bash
# 1. Install dependencies
pip install -r requirements-dev.txt

# 2. Set environment variables (optional)
export MONGO_URI="mongodb://localhost:27017/dyocense"
export OPENAI_API_KEY="your-key-here"
export ALLOW_ANONYMOUS="true"  # For development only

# 3. Run the unified kernel
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001
```

**What you get:**
- All services running at `http://localhost:8001`
- Single API documentation at `http://localhost:8001/docs`
- All endpoints under one domain:
  - `/v1/compile` - Compiler service
  - `/v1/forecast` - Forecasting service
  - `/v1/optimise` - Optimization service
  - `/v1/policy` - Policy evaluation
  - `/v1/diagnose` - Diagnostics
  - `/v1/explain` - Explanation generation
  - `/v1/evidence` - Evidence persistence
  - `/v1/runs` - Orchestrator (legacy & plan modes)
  - `/v1/plan` - Planner service (new)
  - `/v1/accounts/*` - Authentication
  - `/api/accounts/*` - Accounts (back-compat)

### Option 2: Docker Compose (Production-like)

```bash
# Start all services with Docker
docker-compose -f docker-compose.smb.yml up -d

# View logs
docker-compose -f docker-compose.smb.yml logs -f

# Check health
curl http://localhost:8001/healthz

# Stop services
docker-compose -f docker-compose.smb.yml down
```

### Option 3: Quick Start Script

```bash
# Automated setup with health checks
./scripts/quickstart_smb.sh
```

---

## 🧪 Development Setup

### Running with Auto-Reload

```bash
# Terminal 1: Backend
cd /Users/balu/Projects/dyocense
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001

# Terminal 2: Frontend (if needed)
cd apps/ui
npm install
npm run dev
```

### Running Tests

```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_plan_mode.py -v

# With coverage
python -m pytest --cov=packages --cov=services

# Just the planner tests
python -m pytest tests/test_plan_mode.py::test_planner_create_and_execute_basic_plan -v
```

---

## 🔧 Service Architecture

### Before Refactor
```
services/kernel/          → Partial aggregator
services/kernel_unified/  → Full aggregator (duplicate)
```

### After Refactor
```
services/kernel/          → Single unified entrypoint
  ├─ Includes all sub-services via include_router
  ├─ Planner integration (new)
  └─ Back-compat accounts mount

services/kernel_unified/  → Deprecated shim (logs warning)
```

---

## 📋 Environment Variables

### Required
```bash
# Database (optional in dev, uses in-memory fallback)
MONGO_URI=mongodb://localhost:27017/dyocense

# OR PostgreSQL (SMB mode)
POSTGRES_URI=postgresql://dyocense:password@localhost:5432/dyocense
```

### Optional - AI/LLM
```bash
# For LLM-powered features
OPENAI_API_KEY=sk-...
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com
AZURE_OPENAI_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Optional - Authentication
```bash
# Development mode (bypasses auth)
ALLOW_ANONYMOUS=true

# JWT configuration
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Keycloak (enterprise)
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=dyocense
KEYCLOAK_CLIENT_ID=dyocense-api
```

### Optional - Planner Configuration
```bash
# Timeouts for plan execution (seconds)
PLAN_FORECAST_TIMEOUT_SEC=15
PLAN_OPTIMISE_TIMEOUT_SEC=30

# Enable/disable tracing
PLAN_ENABLE_TRACING=1
```

### Optional - Optimizer Backend
```bash
# Choose solver: ortools (default), pyomo, or stub
OPTIMISER_BACKEND=ortools
```

---

## 🧩 New Planner Service

### What's New?

The planner service provides **structured multi-step plan execution**:

1. **Draft Plans** - Define step DAGs with dependencies
2. **Execute Plans** - Run steps in correct order with artifact persistence
3. **Reference Resolution** - Automatically chain outputs between steps
4. **Tracing** - JSONL trace events for observability
5. **Fallback Handling** - Graceful degradation when steps fail

### Example: Create and Execute a Plan

```bash
# 1. Create a plan
curl -X POST http://localhost:8001/v1/plan \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Minimize inventory cost while meeting demand",
    "template_id": "inventory_basic",
    "horizon": 3,
    "series": [
      {"name": "sku_A", "values": [10, 12, 15]},
      {"name": "sku_B", "values": [5, 6, 7]}
    ]
  }'

# Response includes plan_id: "plan-abc123"

# 2. Execute the plan
curl -X POST http://localhost:8001/v1/plan/execute/plan-abc123

# 3. Check status
curl http://localhost:8001/v1/plan/plan-abc123

# 4. View artifacts
ls -la artifacts/plans/plan-abc123/
# forecast.json, policy.json, solution.json, diagnostics.json, 
# explanation.json, evidence.json, trace.jsonl
```

### Plan Mode via Orchestrator

The orchestrator now supports two modes:

```bash
# Legacy mode (old behavior)
curl -X POST http://localhost:8001/v1/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{
    "goal": "Optimize inventory",
    "template_id": "inventory_basic",
    "mode": "legacy"
  }'

# Plan mode (new structured execution)
curl -X POST http://localhost:8001/v1/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{
    "goal": "Optimize inventory",
    "template_id": "inventory_basic",
    "mode": "plan"
  }'
```

---

## 📊 Health Checks

### Basic Health
```bash
curl http://localhost:8001/healthz
# {"status": "ok"}
```

### Detailed Health
```bash
curl http://localhost:8001/health/detailed
# Includes persistence, authentication, and service status
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check Python version (3.10+)
python --version

# Check dependencies
pip install -r requirements-dev.txt

# Check port availability
lsof -i :8001
```

### Tests Failing

```bash
# Ensure you're in project root
cd /Users/balu/Projects/dyocense

# Configure Python environment first
export PYTHONPATH=.

# Run with verbose output
python -m pytest -vv
```

### Import Errors

```bash
# Make sure PYTHONPATH includes project root
export PYTHONPATH=/Users/balu/Projects/dyocense

# Or run from project root
cd /Users/balu/Projects/dyocense
PYTHONPATH=. uvicorn services.kernel.main:app --reload
```

### Planner Execution Fails

```bash
# Check artifacts directory exists
ls -la artifacts/plans/

# Enable tracing for debugging
export PLAN_ENABLE_TRACING=1

# Check timeout settings
export PLAN_FORECAST_TIMEOUT_SEC=30
export PLAN_OPTIMISE_TIMEOUT_SEC=60

# View plan status and risks
curl http://localhost:8001/v1/plan/<plan-id> | jq '.risks'
```

### Authentication Issues

```bash
# For development, bypass auth
export ALLOW_ANONYMOUS=true

# Or use demo token
curl -H "Authorization: Bearer demo-tenant" http://localhost:8001/v1/runs
```

---

## 🚀 Deployment

### Docker Build

```bash
# Build unified kernel image
docker build -f Dockerfile.unified -t dyocense:latest .

# Run container
docker run -p 8001:8001 \
  -e MONGO_URI="mongodb://host.docker.internal:27017/dyocense" \
  -e ALLOW_ANONYMOUS="true" \
  dyocense:latest
```

### Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.smb.yml up -d

# View logs
docker-compose -f docker-compose.smb.yml logs -f kernel

# Scale kernel instances (if needed)
docker-compose -f docker-compose.smb.yml up -d --scale kernel=3
```

---

## 📚 Related Documentation

- **Architecture**: `docs/PHASE1_DEPLOYMENT.md`, `docs/PHASE2_IMPLEMENTATION.md`
- **Planner Design**: Check `packages/agent/schemas.py` for PlanPack structure
- **Executor Logic**: `packages/agent/executor.py` for step execution
- **API Reference**: `http://localhost:8001/docs` when running
- **Tests**: `tests/test_plan_mode.py` for usage examples

---

## 🎯 Next Steps

1. **Start the service**: `PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001`
2. **Explore the API**: Visit `http://localhost:8001/docs`
3. **Try the planner**: Create a plan via `/v1/plan` endpoint
4. **Run tests**: `python -m pytest tests/test_plan_mode.py -v`
5. **Deploy with Docker**: Use `docker-compose.smb.yml` for production-like setup

---

## 💡 Tips

- **Single Service**: Everything runs on port 8001 now (no more port conflicts)
- **Auto-Reload**: Use `--reload` flag during development
- **Plan Artifacts**: Check `artifacts/plans/<plan-id>/` for step outputs
- **Tracing**: Use `trace.jsonl` for debugging plan execution
- **Tests Pass**: All 25 tests green after refactor, including 2 new plan-mode tests
