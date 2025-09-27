# Local Development Environment

Phase 0 services share a common sandbox that relies on containerised dependencies. To get a clean stack:

1. **Start the full stack (dev mode)**
   ```bash
   make dev
   ```
   (Equivalent to `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build`).
   This launches MongoDB, Redis, Neo4j, the kernel (with reload), the unified API, and the Vite dev server. Source code changes in `kernel/`, `api/`, and `client/` hot‑reload automatically.

   Exposed ports:

   - Kernel API → <http://localhost:8080>
   - Backend API → <http://localhost:8000>
   - Client UI → <http://localhost:3000>

2. **Environment variables when running processes manually**
   If you prefer to run Python apps outside Docker, export the same variables used by Compose so the backend can reach Mongo, Redis, Neo4j, and the kernel:
   ```bash
   export PLAN_MONGO_URI="mongodb://localhost:27017"
   export PLAN_MONGO_DB="dyocense"
   export PLAN_MONGO_COLLECTION="plans"
   export PLAN_KERNEL_BASE_URL="http://localhost:8080"  # point to the running kernel API
   ```
   Goal module variables are similar:
   ```bash
   export GOAL_MONGO_URI="mongodb://localhost:27017"
   export GOAL_MONGO_DB="dyocense"
   export GOAL_MONGO_COLLECTION="goals"
   export GOAL_KERNEL_BASE_URL="http://localhost:8080"
   export GOAL_PLAN_SERVICE_URL="http://localhost:8000"
   export SCHEDULER_MONGO_URI="mongodb://localhost:27017"
   export SCHEDULER_MONGO_DB="dyocense"
   export SCHEDULER_JOBS_COLLECTION="scheduler_jobs"
   export SCHEDULER_TENANTS_COLLECTION="scheduler_tenants"
   export FEEDBACK_MONGO_URI="mongodb://localhost:27017"
   export FEEDBACK_MONGO_DB="dyocense"
   export FEEDBACK_COLLECTION="feedback_events"
   export FEEDBACK_KERNEL_BASE_URL="http://localhost:8080"
   export FEEDBACK_SCHEDULER_URL="http://localhost:8000"
   export POLICY_MONGO_URI="mongodb://localhost:27017"
   export POLICY_MONGO_DB="dyocense"
   export POLICY_POLICIES_COLLECTION="policies"
   export POLICY_AUDITS_COLLECTION="policy_audits"
   ```
   Replace base URLs with deployed endpoints as needed.

3. **Install Python dependencies**
   ```bash
   pip install -r api/requirements.txt
   ```
   This includes FastAPI, Starlette, the kernel client dependencies, and `pymongo`. For local tests, `mongomock` is bundled to avoid a hard dependency on a live Mongo instance.

4. **Run the consolidated backend manually (optional)**
   ```bash
   uvicorn api.app:app --reload --port 8000
   ```
   All former microservice endpoints are now available from this single
   FastAPI process. Use bearer tokens to simulate tenants (the shared
   middleware accepts any `Authorization: Bearer <tenant_id>` header).

5. **Run kernel unit tests**
   ```bash
   python kernel/tests/test_pipeline.py
   python kernel/tests/test_golden_runs.py
   ```

6. **Optional – module-specific tests**
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
   Tests still rely on `mongomock` unless you point the relevant `*_MONGO_URI`
   variables at a live instance.

Remember to stop the containers when finished:
```bash
make stop
```
