# Scheduler Service — DESIGN

## Responsibility
Provide tenant-aware weighted fair-queuing (WFQ) scheduling, track budgets/rate limits, and dispatch work to kernel workers.

## API (MVP)
- `POST /queue/enqueue` — enqueue a job `{tenant_id, tier, payload, cost_estimate}`
- `POST /queue/lease` — lease jobs for a worker (honouring WFQ)
- `POST /queue/{job_id}/heartbeat` — extend lease
- `POST /queue/{job_id}/complete` — mark job done and report usage
- `GET/POST /tenants/{id}/budget` — view/update limits & remaining budgets

## Data Ownership (MongoDB)
Collections: `scheduler_jobs`, `scheduler_tenants`

```json
{
  "job_id": "job_123",
  "tenant_id": "tenant_demo",
  "tier": "pro",
  "job_type": "kernel_run",
  "payload": {...},
  "cost_estimate": {"solver_sec": 2.0},
  "priority": 3,
  "virtual_finish": 10234.5,
  "status": "queued",
  "worker_id": null,
  "lease_expires_at": null,
  "created_at": "2024-09-01T10:00:00Z",
  "updated_at": "2024-09-01T10:00:00Z"
}
```

```json
{
  "tenant_id": "tenant_demo",
  "tier": "pro",
  "weight": 3.0,
  "remaining": {"solver_sec": 1000, "gpu_sec": 500, "llm_tokens": 1.0e6},
  "limits": {"solver_sec": 12000, "gpu_sec": 6000, "llm_tokens": 1.5e9},
  "rate_limit_per_minute": 8,
  "last_request_ts": 1725489600.0
}
```

## Sequences
- **Enqueue**: request → rate-limit check → compute virtual finish using tenant weight/cost → persist job.
- **Lease**: worker requests jobs → WFQ ordering by priority/virtual finish → lease expiry set/in-flight tracking.
- **Complete**: mark job done → decrement tenant usage → expose metrics for Policy Guard dashboards.

## Non-Functionals
- WFQ fairness across tiers, rate limiting per tenant.
- Tracing (OTel) around enqueue/lease/complete operations.
- Security: JWT tenant claims, per-tenant filtering, audit logs for budget changes.
