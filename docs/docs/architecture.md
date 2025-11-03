# 🧭 Dyocense Decision Kernel Platform (DDKP) — CNCF‑First, Agent‑Native Architecture
**Objective:** Build a free‑forever, open‑standards platform for **Goal → Forecast → Optimise → Explain → Learn**, powered by **CNCF** tooling and **GenAI agent integrations** (incl. **MCP — Model Context Protocol**).

---

## 🌍 Vision
Deliver a neutral **Decision Intelligence Kernel** that any agent (ChatGPT, Claude, Copilot, LangChain, MCP clients) can call to produce **optimal, explainable, and policy‑verified plans**.  
Everything is **contract‑first** (OpenAPI + JSON‑Schema), **observable** (OpenTelemetry), and **extensible** (OCI‑packaged archetypes).

---

## 🔑 Principles
- **CNCF‑first**: Prefer graduated/incubating CNCF projects and free OSS.
- **Contract‑driven**: OPS / SolutionPack as stable JSON‑Schema with SemVer.
- **Composability**: Each capability is a microservice/tool (compile, forecast, optimise, explain, diagnose).
- **Multi‑agent ready**: Native support for **MCP**, OpenAI Tools, Anthropic Tool Use, LangChain/LangGraph nodes.
- **Security & Compliance**: OIDC (Keycloak), SPIFFE/SPIRE mTLS, OPA/Kyverno policies, SBOM + signing.
- **Cost‑efficient scale**: KEDA autoscaling on queues; stateless workers; cache where safe.

---

## 🏗️ Reference Architecture (CNCF‑only & free OSS)

### Control Plane
- **Identity & SSO**: Keycloak (OIDC/OAuth2)
- **Service Identity & mTLS**: SPIFFE/SPIRE
- **API Ingress/Gateway**: Envoy Gateway (or Contour)
- **Policy & Admission**: OPA + Kyverno
- **GitOps CI/CD**: Argo CD + Argo Workflows
- **Image Registry & Security**: Harbor (OCI) + Cosign (signing) + CycloneDX SBOM
- **Autoscaling**: KEDA
- **Observability**: OpenTelemetry + Prometheus + Grafana + Loki/Tempo

### Data Plane (Services)
- **Compiler (LLM→OPS)**: orchestrated pipeline with knowledge retrieval, OptiGuide-style playbooks, and LLM routing (vLLM/Ollama local first)
- **Forecast**: REST/gRPC around Holt-Winters (statsmodels today; CSV/MinIO/Sheets ingestion; pluggable for Darts/Prophet/SKTime)
- **Policy**: OPA/Kyverno-backed evaluation of OPS before optimisation
- **Optimiser**: OR‑Tools CBC mixed-integer today with optional Pyomo adapters and warm-start validation; roadmap includes Pyomo + HiGHS/Gurobi adapters
- **Explainer**: LLM summaries (via vLLM/Ollama)
- **Diagnostician**: infeasibility analysis & relaxations
- **Scenario**: Branching what-if manager that clones goal versions, applies overrides, and diffs outcomes
- **Evidence Graph**: Neo4j Community (current implementation; JanusGraph adapter on backlog)
- **Knowledge**: Dataset catalog + retrieval layer (MinIO/Iceberg + Qdrant fallback)
- **Trust & Facts**: a1facts-inspired registry attaching compliance statements to runs
- **Marketplace**: Catalog of archetypes/solvers/connectors served via REST/OCI
- **Orchestrator**: Background workflow that drives compile→forecast→policy→optimise→diagnose→explain→evidence
- **Dashboard**: Single-page UI surfacing runs, artifacts, and evidence (Phase 6 stub)
- **Connectors**: CSV/Google Sheets (start free), Shopify/Woo later

### Storage (Free OSS)
- **MongoDB Community**: metadata, runs, tenancy
- **MinIO**: artifacts/datasets (S3 compatible)
- **Redis OSS**: caching, small queues
- **Neo4j CE**: evidence/ontology graph (JanusGraph adapter follows once the graph abstraction stabilises)
- **NATS JetStream** (or Apache Kafka OSS): events bus (CloudEvents payloads)

---

## 🧩 Open Standards
- **APIs**: OpenAPI 3.1 + JSON‑Schema 2020‑12
- **Events**: CloudEvents 1.0 (on NATS/Kafka + webhooks)
- **Telemetry**: OpenTelemetry traces/metrics/logs
- **Packaging**: OCI bundles for archetypes/solvers/connectors
- **Models**: ONNX/PMML for forecast portability
- **Policy**: Rego (OPA); Kyverno policies
- **Identity**: OIDC/OAuth2; SPIFFE/SPIRE for workload identities

---

## 🧠 GenAI & Agent Integrations (incl. MCP)

### Model Context Protocol (MCP)
**What:** A standardized protocol for LLM apps/agents to talk to local/remote **tools, resources, and prompts**.  
**How we support it:**
- Provide an **MCP Server** exposing tools: `compile`, `optimise`, `forecast`, `explain`, `diagnose`.
- MCP clients (Claude Desktop, VS Code extensions, other agent runtimes) can discover and call these tools.
- Transport: JSON‑RPC over stdio/WebSocket with structured JSON responses.

**Minimal MCP Server Tool (concept):**
```jsonc
{
  "name": "decision_kernel",
  "tools": [
    {
      "name": "compile",
      "description": "Compile natural goal + tables → OPS JSON",
      "inputSchema": { "$ref": "schemas/compile.input.schema.json" }
    },
    {
      "name": "optimise",
      "description": "OPS → SolutionPack",
      "inputSchema": { "$ref": "schemas/ops.schema.json" }
    }
  ]
}
```

### OpenAI Assistants / Tools
- Tool manifest maps to our OpenAPI ⇒ Assistants can call `/v1/optimise` etc.
- We ship a **ready JSON Tool schema** with parameter validation.

### Anthropic Tool Use
- Define `tools=[{name, description, input_schema}]` mirroring our JSON‑Schemas.
- The model returns a `tool_use` with arguments → route to our API, then stream results back.

### LangChain / LangGraph
- Provide `DecisionSolverTool` and graph nodes (`CompileNode`, `ForecastNode`, `SolveNode`, `ExplainNode`).
- Example:
```python
from dyocense import DecisionSolverTool
agent = initialize_agent([DecisionSolverTool()], llm, verbose=True)
agent.run("Build rota for next week under £5k")
```

### VLLM / Ollama
- Local inference for Compiler/Explainer to keep data local and costs low.
- Swap in remote providers later (OpenAI, Anthropic) via config flags.

---

## 🧱 Layered Design (Monorepo)

Phase 0+1 establish the following top-level structure (present in the repository):

```
/
├─ services/                 # Deployable microservices (compiler, forecast, optimiser, explainer, etc.)
├─ packages/
│  └─ contracts/             # Canonical JSON schemas and future OpenAPI specs
├─ infra/                    # Infrastructure as code (Helm, Kustomize, Terraform, etc.)
├─ docs/                     # Architecture, specs, integration guides
├─ examples/                 # Sample OPS/SolutionPack payloads feeding tests
├─ scripts/                  # Developer tooling (validation, scaffolding)
└─ vision.md                 # Manifesto + roadmap
```

As we progress through subsequent phases, the directories below will be populated with concrete services, SDKs, and deployment assets. Each addition must preserve the layering above: **contracts → shared packages → services → infra → docs/examples**.

**Phase 5 status:** `services/compiler`, `services/forecast`, `services/policy`, `services/optimiser`, `services/diagnostician`, `services/explainer`, `services/evidence`, `services/marketplace`, and the new `services/orchestrator` deliver the full Goal → Forecast → Policy → Optimise → Diagnose → Explain loop with evidence logging and catalog selection. SDKs consume the orchestrated flow, while `scripts/phase3_demo.py` remains a reference harness.

A unified `services/kernel` gateway aggregates all routes behind a single FastAPI server for lightweight deployments, including the orchestration endpoints.

**Language choices**
- Python for services (FastAPI) + adapters
- Go optional for high‑throughput gateway helpers
- TypeScript for SDK and tools where helpful

---

## 🔌 Core API Surface (OpenAPI 3.1)
- `POST /v1/compile` → OPS (valid JSON only)
- `POST /v1/optimise` → SolutionPack (decisions + kpis + diagnostics)
- `POST /v1/forecast` → { point, low, high, model }
- `POST /v1/explain` → { summary, what_ifs }
- `POST /v1/diagnose` → { relaxations[] }
- `GET  /v1/catalog` → archetypes, solvers, connectors
- `GET  /v1/runs/:id` → status, artifacts, traces

All endpoints return **trace ids** (OTel) and emit **CloudEvents**.

---

## 🔐 Security & Policy
- **AuthN**: Keycloak (OIDC), PATs for dev
- **AuthZ**: OPA (Rego policies) + Envoy ext_authz
- **Workload mTLS**: SPIFFE/SPIRE
- **Admission & Runtime**: Kyverno policies (resource quotas, image signatures)
- **Secrets**: Kubernetes Secrets sealed w/ external KMS (e.g., HashiCorp Vault OSS if needed)
- **Data residency**: namespace/cluster‑per‑region; S3 buckets per tenant/region

Phase 4–5 stubs: FastAPI services enforce bearer tokens via `packages.kernel_common.auth`, SDKs consume the REST surface, and Kustomize manifests under `infra/k8s/base` spin up Keycloak, MongoDB, NATS, and the marketplace service for local experimentation.

---

## 📊 Observability & SLOs
- **Traces**: OpenTelemetry across compile→solve→explain; Grafana Tempo/Jaeger
- **Metrics**: Prometheus; p50/p95, success rate, optimality gap
- **Logs**: Loki with labels {tenant, service, run_id}
- **Events**: CloudEvents on NATS topics; user webhooks

SLOs (Pro): 99.9% API; 95% solves ≤ 30s (S‑size models).

---

## 🧪 Validation & QA
- JSON‑Schema validators for OPS/Pack
- Golden problems per archetype (inventory, staffing, VRP)
- Regression suite for compiler validity, feasibility rate, runtime, gap
- Static analysis & SBOM; cosign verification in CI

---

## 🧰 MCP & Tooling: Minimal Specs

**MCP Server declaration (YAML)**
```yaml
server:
  name: dyocense-decision-kernel
  version: 1.0.0
tools:
  - name: compile
    input_schema: schemas/compile.input.schema.json
  - name: optimise
    input_schema: schemas/ops.schema.json
  - name: explain
    input_schema: schemas/explain.input.schema.json
transport: stdio
```

**OpenAI Tool (JSON)**
```json
{
  "name": "decision_kernel",
  "description": "Compile, forecast, and optimise business goals into plans.",
  "parameters": {
    "type": "object",
    "properties": { "goal": { "type": "string" }, "data_url": { "type": "string" } },
    "required": ["goal"]
  }
}
```

**LangGraph Node (pseudo)**
```python
class SolveNode(WorkflowNode):
    def call(self, state):
        ops = state["ops"]
        return client.optimise(ops)
```

---

## 🚀 Local Dev (free‑OSS only)
- `docker compose up` for: MongoDB, Neo4j CE, NATS, Keycloak (MinIO/Redis arrive in later phases)
- `make dev` → runs compiler/forecast/optimiser services with hot reload
- `make e2e` → spins sample flow on examples/*.json

---

## 🧭 Roadmap (CNCF Edition)
- **MVP (4–6 weeks)**: OPS/Pack schemas; `/optimise`; OR‑Tools adapter; OpenTelemetry; NATS CloudEvents; MCP server PoC; OpenAI Tool
- **v0.2**: Forecast service; Explain service; Policy (OPA) injection; LangGraph nodes
- **v0.3**: Evidence Graph; OCI archetype packaging; Helm charts; Argo CD apps
- **v0.4**: Multi‑tenant hardening; SPIFFE/SPIRE; Envoy ext_authz; Kyverno policies
- **v1.0**: Marketplace; connectors; SDKs; docs & examples

---

## 📜 Licensing
- **Core & specs**: Apache‑2.0
- **Helm charts, manifests, SDKs**: Apache‑2.0
- Optional enterprise add‑ons may be licensed separately in future.

---

## ✨ Tagline
**Dyocense — The CNCF‑native Decision Kernel for GenAI Agents (with MCP).**
