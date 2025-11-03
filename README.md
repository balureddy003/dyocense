<<<<<<< HEAD
# 🧭 Dyocense Decision Kernel Platform (DDKP)
**Open-standard Decision Intelligence for the Agent Economy**

Dyocense is a cloud-native framework that turns **natural-language goals** into **optimal, explainable, verifiable decisions** by combining **LLMs + Forecasting + Operational Research (OR)**.

**Core loop:** Goal → Forecast → Optimise → Explain → Learn

- **LLM Compiler**: translates goals + tables into an Optimization Problem Spec (**OPS**).
- **Forecast Engine**: optional time-series predictions injected into parameters.
- **OR Solver**: OR-Tools / Pyomo / HiGHS/Gurobi to find feasible/optimal plans.
- **Explainer**: natural-language summary, trade-offs, and what-ifs.
- **Evidence Graph**: plan→outcome lineage, KPIs, policy verification.
- **APIs/SDKs/Tools**: REST, gRPC, LangChain Tool, ChatGPT/Copilot connectors.

Standards: **OpenAPI 3.1**, **JSON-Schema 2020-12**, **CloudEvents**, **OpenTelemetry**, **OCI**, **ONNX/PMML**.

See `/docs` for full specifications and `vision.md` for the long-term manifesto.

---

## Phase 5 (Ecosystem & Marketplace)

We are now in **Phase 5**, expanding ecosystem integrations with SDKs, marketplace catalogues, and evidence dashboards while retaining the hardened control plane foundations from Phase 4.

### Repository layout

```
/
├─ services/             # Deployable microservices (compiler, forecast, optimiser, etc.)
├─ packages/             # Shared libraries and SDKs (contracts live here)
├─ infra/                # Infrastructure manifests and automation
├─ docs/                 # Architecture, specs, integration guides
├─ examples/             # Sample OPS/SolutionPack payloads
├─ scripts/              # Tooling for validation and developer workflows
└─ vision.md             # Product manifesto and roadmap
```

### Contracts
- `packages/contracts/schemas/ops.schema.json` and `solution_pack.schema.json` are the canonical schemas.
- `packages/contracts/openapi/decision-kernel.yaml` describes the compile/forecast/optimise/explain/policy/diagnose API surface.
- `packages/contracts/mcp/tools.json` is the Phase 5 MCP manifest for agent integrations.
- Example payloads reside in `examples/`.
- Schema validation tooling lives in `scripts/validate_ops.py`.

### Services (Phase 4 stubs)
- `services/compiler` exposes `/v1/compile` via FastAPI. It uses the configured LLM to build OPS JSON (falls back to deterministic stub).
- `services/forecast` exposes `/v1/forecast` via FastAPI with Holt-Winters smoothing (auto-detected trend/seasonality and configurable per-series) plus a naive fallback when statsmodels is unavailable.
- `services/policy` exposes `/v1/policy/evaluate` via FastAPI and simulates OPA checks.
- `services/optimiser` exposes `/v1/optimise` via FastAPI, running OR-Tools or Pyomo (configurable) with warm-start hints and KPI validation, and falls back to deterministic solutions when solvers are unavailable.
- `services/diagnostician` exposes `/v1/diagnose` via FastAPI and offers canned relaxation suggestions.
- `services/explainer` exposes `/v1/explain` via FastAPI and provides templated summaries enriched with policy/diagnostics context.
- `services/evidence` exposes `/v1/evidence/log` via FastAPI and stores artefacts in MongoDB while streaming run metadata into the Neo4j evidence graph (falls back to in-memory if either backing store is unavailable).
- `services/marketplace` exposes `/v1/catalog` via FastAPI and publishes available archetypes, solvers, and connectors.
- `services/orchestrator` exposes `/v1/runs` and `/v1/runs/{id}` for a unified goal→decision pipeline with background execution, accepting catalog-driven `archetype_id` and structured `data_inputs` payloads.

All endpoints now expect a bearer token (stubbed via `packages/kernel_common/auth.py`). Use `Authorization: Bearer demo-<tenant>` for local development; set `ALLOW_ANONYMOUS=true` to bypass checks if needed.

### SDKs & Tooling
- `packages/sdk-python` — pip-installable client wrapper (`pip install -e packages/sdk-python`).
- `packages/sdk-typescript` — TypeScript client published via npm workspaces (`npm install --workspace packages/sdk-typescript`).
- `packages/contracts/mcp/tools.json` — Phase 5 MCP manifest including catalog access.
- Orchestration helpers surface `submit_run`/`get_run` so clients can trigger the entire pipeline via `/v1/runs`.
- `tools/postman/Dyocense.postman_collection.json` — Postman collection pointing at `{{baseUrl}}` (defaults to `http://localhost:8001`) with bearer auth (`{{token}} = demo-tenant`) so you can try endpoints interactively.

Run the unified kernel locally (single port for all endpoints):

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001
```

Open Swagger UI at http://localhost:8001/docs (use `demo-tenant` bearer token to "Authorize" and try endpoints).

Or run the orchestration API standalone:

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.orchestrator.main:app --reload --port 8010
```

When triggering `/v1/runs`, include the `archetype_id` (e.g. `inventory_basic`) and optional `data_inputs` payload matching the catalog description (demand, holding cost, etc.).

Alternatively, run individual services:

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.compiler.main:app --reload --port 8002
PYTHONPATH=. uvicorn services.optimiser.main:app --reload --port 8003
PYTHONPATH=. uvicorn services.forecast.main:app --reload --port 8004
PYTHONPATH=. uvicorn services.explainer.main:app --reload --port 8005
PYTHONPATH=. uvicorn services.policy.main:app --reload --port 8006
PYTHONPATH=. uvicorn services.diagnostician.main:app --reload --port 8007
PYTHONPATH=. uvicorn services.evidence.main:app --reload --port 8008
PYTHONPATH=. uvicorn services.marketplace.main:app --reload --port 8009
PYTHONPATH=. uvicorn services.orchestrator.main:app --reload --port 8010
```

Run validation and tests with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
make validate
make test  # requires FastAPI dependencies
python scripts/phase3_demo.py  # writes demo artefact without running HTTP servers
```

`make validate` ensures OPS examples adhere to the schema. `make test` performs an end-to-end compile→forecast→policy→optimise→diagnose→explain flow using FastAPI test clients and exercises the auth/evidence paths.

> **Note:** Advanced forecasting and optimisation require optional dependencies (`numpy`, `pandas`, `statsmodels`, `ortools`, `pyomo`, `neo4j`). These are already listed in `requirements-dev.txt`; install them to enable Holt-Winters forecasting, OR-Tools/Pyomo solving, and graph persistence. Without them, the services automatically fall back to their deterministic stubs.

> **Optional LLM:** Set `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`) to have the explainer service generate narratives using OpenAI's API. Without it, templated summaries are returned.

For local-only LLMs, set `LLM_PROVIDER=ollama` (default) and run an Ollama server with your preferred model (`OLLAMA_MODEL`, default `llama3.1`). Example: `ollama run llama3.1`.

> **Optimiser backends:** Set `OPTIMISER_BACKEND=pyomo` (default `ortools`) and specify `PYOMO_SOLVER` (e.g. `cbc`, `glpk`, `appsi_highs`) to route optimisation through Pyomo. Requests can include a `warm_start` SolutionPack to seed solvers; diagnostics report whether the new objective improves on the warm start.

> **Forecast tuning:** Supply per-series `seasonal`, `seasonal_periods`, `trend`, and `damped` fields in `/v1/forecast` requests to fine-tune Holt-Winters smoothing. Use `FORECAST_DEFAULT_SEASONAL_PERIOD` to override the auto-detected seasonal window globally. Alternatively provide `data_sources` (CSV, MinIO, Sheets) to hydrate series on the fly.

> **Evidence Graph:** To enable Neo4j persistence, set `NEO4J_URI` (e.g. `bolt://localhost:7687`) plus `NEO4J_USER` / `NEO4J_PASSWORD`. Without these env vars (or if the driver is missing), the evidence service keeps operating with the in-memory fallback.

> **Mongo auth:** MongoDB images in `infra/docker-compose`/K8s ship with credentials. Export `MONGO_URI` (or `MONGO_USERNAME`/`MONGO_PASSWORD` alongside `MONGO_HOST`) so services like evidence and kernel can authenticate instead of falling back to the in-memory store. For MinIO-backed forecast ingestion, set `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, and `MINIO_SECRET_KEY`.

Kubernetes manifests now live under `infra/k8s/base`. Deploy them to a local cluster with `kubectl apply -k infra/k8s/base` (images are placeholders).

Bring up a kind cluster and apply the manifests automatically via:

```bash
make kind-up
```

To run dependencies + the unified kernel via Docker Compose:

```bash
docker compose -f infra/docker-compose/docker-compose.yaml up --build
```
(Orchestrator is exposed on port `8010` in the compose stack.)
Run Ollama on your host (e.g., `ollama serve` with `ollama run llama3.1`) and set `OLLAMA_BASE_URL` / `OLLAMA_MODEL` as needed.
The stack also provisions Neo4j (ports `7474` HTTP, `7687` Bolt) with default credentials `neo4j/neo4j123` and MinIO (S3 API `9000`, console `9001`) with `minioadmin/minioadmin`; update the compose file or set env overrides if you need different secrets.

### Dashboard (Stub)
- `apps/dashboard` provides a combined view of runs and evidence; serve it with `python -m http.server 4200 --directory apps/dashboard`.

Set `SKIP_PIP=1` when invoking make targets if you have already installed dependencies (useful in air-gapped environments).

---

## Documentation
- `docs/docs/architecture.md` — CNCF-first architecture blueprint and phase plan.
- `vision.md` — Long-term vision, roadmap, and differentiation pillars.

Future phases will expand each service directory with implementation guides, add SDKs under `packages/`, and introduce IaC in `infra/`.
=======
# The open-standard Decision Kernel that powers intelligent planning for any AI agent.

This repo contains high‑level architecture, data model, tool schemas, and storyboards for the Dyocense platform.

- **Platform core**: Goal → Plan → Execute (domain‑agnostic)
- **MVP1**: Sports Planner (Parents/Kids)
- **MVP2**: Restaurant Copilot (Inventory/Waste)
- **Extensibility**: Packs, Connectors (MCP), Marketplace
- **Runtime**: 2‑tier (Frontend + Backend) with MongoDB **or** SaaS split (Vercel UI + FastAPI + Postgres).

Quick links:
- `docs/dyocense_platform_architecture.md`
- `docs/data_model_domain_agnostic.md`
- `docs/tool_schemas_and_mcp.md`
- `docs/mvp1_sports_planner.md`
- `docs/mvp2_restaurant_copilot.md`
- `docs/deployment_and_scaling.md`
>>>>>>> 6cb3ef8471d1c704b9ddb6eaf687a0c68513d6c0
