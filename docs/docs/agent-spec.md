# Dyocense Decision Agent — End-to-End Build Spec

## Personas & Use-cases
Agent builders, SME SaaS vendors, enterprise AI teams. Archetypes: Inventory, Staffing, VRP, Cash-flow.

## Graph (LangGraph/Crew)
Start → IntentClassifier → DataPrep → CompilerLLM → ValidateOPS → Enrichment(Forecast) → Policy(OPA/a1facts) → Solve(OR) → Diagnose(if infeasible) → ExplainLLM → EvidenceStore → Catalog Feedback → End

## Contracts
- **OPS (`ops.v1`)**: objective, variables, parameters, constraints, kpis, metadata, validation_notes.
- **SolutionPack (`pack.v1`)**: status, objective_value, decisions, kpis, diagnostics, explanation_hints, artifacts.

## APIs
- POST /v1/compile → OPS
- POST /v1/forecast → forecast
- POST /v1/policy/evaluate → policy verdict + checks
- POST /v1/optimise → SolutionPack
- POST /v1/diagnose → relaxations
- POST /v1/explain → narrative + what-ifs
- POST /v1/evidence/log → persist run artefacts
- GET  /v1/evidence → list evidence records (tenant scoped)
- GET /v1/catalog, GET /v1/runs/{id}
- POST /v1/runs → orchestrate full pipeline (requires `archetype_id`, optional `data_inputs`)
- GET /v1/runs → list orchestrated runs

All endpoints are exposed both individually and through the unified `kernel-api` FastAPI deployment (single port) for lightweight integrations.
## LLM Prompts (canonical)
- Compiler (system): “Convert user goals + tables into **valid OPS JSON** per JSON-Schema. Choose archetype. Output JSON only.”
- Explainer (system): “Explain decisions in plain English. Summarise trade-offs, binding constraints, what-ifs.”

## Solver Adapters
Interface: build(ops) → solve(time_limit) → extract(). Adapters: OR-Tools CP-SAT, Pyomo+HiGHS/Gurobi. Safe expression parser to AST (no eval).

## Forecast Plug-ins
`forecast(series, horizon, exogenous=None, strategy="auto") → {point, low, high, model}`

## Policy & Knowledge
a1facts ontology for domain entities; OPA/Rego for mandatory constraints; infeasibility diagnostician proposes ranked relaxations.

## Security & SLOs
OIDC auth, tenant RBAC, region pinning, RLS; OTel tracing; 95% solves ≤30s (S-size).

See `packages/contracts/schemas`, `packages/contracts/openapi`, `packages/contracts/mcp`, and the new SDKs under `packages/sdk-python` & `packages/sdk-typescript` for canonical contracts and clients.
