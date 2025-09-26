# Local Development Environment

Phase 0 services share a common sandbox that relies on containerised dependencies. To get a clean stack:

1. **Bootstrap infrastructure**
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```
   This starts Redis (queue/cache), MongoDB (service persistence) and Neo4j (evidence graph). All data volumes are persisted locally (`mongo_data`, `neo4j_data`).

2. **Set environment variables**
   For each service (for example, the Plan service) export the following:
   ```bash
   export PLAN_MONGO_URI="mongodb://localhost:27017"
   export PLAN_MONGO_DB="dyocense"
   export PLAN_MONGO_COLLECTION="plans"
   export PLAN_KERNEL_BASE_URL="http://localhost:8080"  # point to the running kernel API
   ```
   Replace the base URL with the location of your kernel deployment or local run.

3. **Install Python dependencies**
   ```bash
   pip install -r services/requirements.txt
   ```
   This includes FastAPI, Starlette, the kernel client dependencies, and `pymongo`. For local tests, `mongomock` is bundled to avoid a hard dependency on a live Mongo instance.

4. **Run the Plan service locally**
   ```bash
   uvicorn services.plan.app:app --reload --port 8001
   ```
   Use bearer tokens to simulate tenants (the default middleware accepts any `Authorization: Bearer <tenant_id>` header).

5. **Run kernel unit tests**
   ```bash
   python kernel/tests/test_pipeline.py
   python kernel/tests/test_golden_runs.py
   ```

6. **Optional – run Plan service tests**
   ```bash
   python -m pytest services/plan/tests
   ```
   Requires `PLAN_MONGO_URI` pointing at the dev MongoDB or relies on the built-in `mongomock` when not available.

Remember to stop the containers when finished:
```bash
docker compose -f docker-compose.dev.yml down
```
