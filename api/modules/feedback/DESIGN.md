# Feedback Service — DESIGN

## Responsibility
Ingest actual demand/lead-time data, update forecasting feedback caches, and trigger replans while exposing KPI drift summaries.

## API (MVP)
- `POST /feedback/ingest` — upload actuals `{goal_id?, plan_id?, actuals[]}`
- `GET /feedback/kpi-drift` — aggregate drift report per SKU (optional `goal_id` filter)

## Data Ownership (MongoDB)
Collection: `feedback_events`

```json
{
  "event_id": "event_123",
  "tenant_id": "tenant_demo",
  "goal_id": "goal_1",
  "plan_id": "plan_1",
  "actuals": [
    {"sku": "SKU1", "period": "2025-09-01", "quantity": 120, "lead_time_days": 2}
  ],
  "created_at": "2025-09-05T12:00:00Z"
}
```

## Sequences
- **Ingest**: authenticate → persist actuals → call Kernel `/forecast/feedback` → optionally enqueue Scheduler job → respond with counters.
- **Drift report**: aggregate historical actuals by SKU; expose average and last observation for dashboards.

## Non-Functionals
- idempotent ingestion via upstream keys (future), <100 ms targets for drift.
- Tracing & metrics around ingestion (requests/sec, kernel feedback success rate).
- Security: JWT tenant context, per-tenant document filtering.
