# Plan Service — DESIGN

## Responsibility
Orchestrate OptiGuide+Optimizer; produce plans with KPIs & steps.

## API (MVP)
- POST /plans {goal_id, variant, kernel_payload}
- POST /plans/{id}/delta {variant_suffix?, kernel_payload}
- POST /plans/{id}/counterfactual {variant_suffix?, kernel_payload}
- GET /plans
- GET /plans/{id}
- GET /plans/{id}/steps
- GET /plans/{id}/evidence

## Data Ownership (MongoDB)
Collection: `plans`

Document shape (simplified):
```json
{
  "plan_id": "uuid",
  "tenant_id": "tenant_demo",
  "goal_id": "goal-123",
  "variant": "baseline",
  "request_payload": {...},
  "result": {
    "evidence_ref": "evidence://...",
    "solution": {"status": "FEASIBLE", "steps": [...]},
    "diagnostics": {"simulation": {...}, "robust_eval": {...}},
    "policy": {"allow": true, "policy_id": "policy.guard.v1"}
  },
  "created_at": "2024-08-12T19:32:11.123Z"
}
```
## Sequences
- On create: authenticate → enrich kernel payload with tenant tier → run kernel pipeline → persist result (policy snapshot + diagnostics) → trace span.
- On delta/counterfactual: load baseline plan → merge overrides → run kernel pipeline (mode tagged) → persist new plan with `parent_plan_id` → trace span.
- On read: enforce tenant scope, list history, expose diagnostics and evidence references.

## Non‑Functionals
- P50 read < 50ms, P95 < 200ms; idempotent POST with request keys.
- Tracing (OTel), metrics (Prometheus), logs (JSON).
- Security: Keycloak JWT, OPA checks, per‑tenant row scoping.
