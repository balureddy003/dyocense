# Goal Service — DESIGN

## Responsibility
Capture business intent (GoalDSL + context) for each tenant, manage variants and approvals, validate policy constraints, and trigger planning when goals reach execution-ready states.

## API (MVP)
- `POST /goals` — create draft goal + baseline GoalDSL
- `GET /goals` — list goals for tenant
- `GET /goals/{id}` — fetch goal details, variants, approvals, feedback
- `PATCH /goals/{id}` — update name/GoalDSL/context
- `POST /goals/{id}/variants` — add variant overrides
- `POST /goals/{id}/validate` — run Policy Guard check-only compile
- `POST /goals/{id}/status` — transition workflow (`draft → pending → ready`) and emit plan trigger
- `POST /goals/{id}/feedback` — ingest actuals and request re-plan

## Data Ownership (MongoDB)
Collection: `goals`

```json
{
  "goal_id": "goal_123",
  "tenant_id": "tenant_demo",
  "name": "Inventory Planning",
  "goaldsl": {...},
  "context": {...},
  "variants": [
    {"variant_id": "var_1", "name": "high-service", "goaldsl": {...}, "context": {...}}
  ],
  "status": "READY_TO_PLAN",
  "approvals": [
    {"status": "READY_TO_PLAN", "note": "Auto-approved", "timestamp": "2024-09-01T10:00:00Z"}
  ],
  "feedback": [
    {"actuals": {"SKU1": 120}, "note": "September actuals", "timestamp": "2024-09-10T12:00:00Z"}
  ],
  "created_at": "2024-08-12T19:32:11Z",
  "updated_at": "2024-09-10T12:00:00Z"
}
```

## Sequences
- **Create**: authenticate → persist GoalDSL/context in `draft`. Variants optional.
- **Validate**: call Kernel compile in check-only mode (no solve) → return `policy_snapshot` + metadata to UI.
- **Approve**: update status to `READY_TO_PLAN` → trigger Plan service webhook (auto baseline solve) → record approval trail.
- **Feedback**: store actuals, optionally annotate, and re-trigger plan generation for follow-up run.

## Non‑Functionals
- P50 read < 50 ms, P95 < 200 ms; writes idempotent on `goal_id`.
- Tracing (OTel), metrics (Prometheus), structured JSON logs.
- Security: Keycloak JWT, Policy Guard validation, per-tenant document filters.
