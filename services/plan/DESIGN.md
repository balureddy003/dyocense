# Plan Service — DESIGN

## Responsibility
Orchestrate OptiGuide+Optimizer; produce plans with KPIs & steps.

## API (MVP)
- POST /plans {goal_id, variant} -> plan
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
- On create: validate JWT→OPA allow→persist→emit domain event→trace span.
- On read: enforce tenant scope, paginate, cache as needed.

## Non‑Functionals
- P50 read < 50ms, P95 < 200ms; idempotent POST with request keys.
- Tracing (OTel), metrics (Prometheus), logs (JSON).
- Security: Keycloak JWT, OPA checks, per‑tenant row scoping.
