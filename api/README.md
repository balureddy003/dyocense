# Running Services Locally

Every service shares the Phase-0 foundations documented in `docs/LOCAL_DEV.md`. Below is a quick reference for debugging individual services on your machine.

## 1. Prerequisites

1. Start local dependencies:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```
   (Redis, MongoDB, Neo4j.)

2. Launch the kernel REST API (adjust to your entrypoint):
   ```bash
   uvicorn kernel.api:app --reload --port 8080
   ```

3. If your virtualenv was created without `pip`, bootstrap it:
   ```bash
   python -m ensurepip --upgrade
   python -m pip install --upgrade pip
   ```

4. Install service dependencies (kernel + backend share the same set):
   ```bash
   pip install -r api/requirements.txt
   ```

## 2. Environment Variables

Export environment variables for the consolidated backend (they retain the
existing prefixes so you can migrate gradually):

```bash
# Kernel + Backend
export PLAN_MONGO_URI="mongodb://localhost:27017"
export PLAN_MONGO_DB="dyocense"
export PLAN_MONGO_COLLECTION="plans"
export PLAN_KERNEL_BASE_URL="http://localhost:8080"

# Optional LLM integration (shared across services)
export LLM_BASE_URL="http://localhost:9000"   # e.g. llm-router or OpenAI-compatible endpoint
export LLM_MODEL="gpt-4o-mini"
export LLM_API_KEY="sk-demo"
# When not configured the kernel falls back to deterministic summaries, so these are optional during local dev.

# Goal module
export GOAL_MONGO_URI="mongodb://localhost:27017"
export GOAL_MONGO_DB="dyocense"
export GOAL_MONGO_COLLECTION="goals"
export GOAL_KERNEL_BASE_URL="http://localhost:8080"
export GOAL_PLAN_SERVICE_URL="http://localhost:8001"

# Evidence module
export EVIDENCE_MONGO_URI="mongodb://localhost:27017"
export EVIDENCE_MONGO_DB="dyocense"
export EVIDENCE_COLLECTION="evidence_snapshots"

# Feedback module
export FEEDBACK_MONGO_URI="mongodb://localhost:27017"
export FEEDBACK_MONGO_DB="dyocense"
export FEEDBACK_COLLECTION="feedback_events"
export FEEDBACK_KERNEL_BASE_URL="http://localhost:8080"
export FEEDBACK_SCHEDULER_URL="http://localhost:8003"

# Scheduler module
export SCHEDULER_MONGO_URI="mongodb://localhost:27017"
export SCHEDULER_MONGO_DB="dyocense"
export SCHEDULER_JOBS_COLLECTION="scheduler_jobs"
export SCHEDULER_TENANTS_COLLECTION="scheduler_tenants"

# Policy module
export POLICY_MONGO_URI="mongodb://localhost:27017"
export POLICY_MONGO_DB="dyocense"
export POLICY_POLICIES_COLLECTION="policies"
export POLICY_AUDITS_COLLECTION="policy_audits"

# Market module
export MARKET_MONGO_URI="mongodb://localhost:27017"
export MARKET_MONGO_DB="dyocense"
export MARKET_COLLECTION="market_intel"

# Negotiation module
export NEGOTIATION_PLAN_SERVICE_URL="http://localhost:8000"
```

## 3. Launch Services (examples)

Run the consolidated backend (one FastAPI process that exposes all routes):

```bash
uvicorn api.app:app --reload --port 8000
```

For debugging a specific module in isolation you can still start the module
routers directly (e.g. `uvicorn api.modules.plan.app:app --port 8001`).

## 4. Run Command from Project Root

All commands above assume you are inside the project root (`/path/to/dyocense`). For example:
```bash
cd /path/to/dyocense
python -m uvicorn kernel.api:app --reload --port 8080
```

## 5. Useful Samples

HTTPie examples live under `scripts/`: `httpie_samples.md`, plus service-specific folders (`scripts/goals`, `scripts/feedback`, `scripts/policy`, `scripts/scheduler`, `scripts/market`).

## 6. Running Tests

Tests rely on `mongomock` (installed via requirements). Run individual suites with:

```bash
python -m pytest api/tests
python -m pytest api/modules/plan/tests
python -m pytest api/modules/goal/tests
python -m pytest api/modules/evidence/tests
python -m pytest api/modules/feedback/tests
python -m pytest api/modules/policy/tests
python -m pytest api/modules/scheduler/tests
python -m pytest api/modules/market/tests
```

Kernel tests remain available via `python kernel/tests/test_pipeline.py` and `python kernel/tests/test_golden_runs.py`.

## 7. Client Stub

The `client/` folder contains a placeholder FastAPI app that currently serves
a static status page. Run it with `uvicorn client.app:app --reload --port 3000`
while developing end-user workflows.

## 8. Shut Down

```bash
docker compose -f docker-compose.dev.yml down
```
