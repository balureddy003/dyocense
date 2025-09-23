# Scheduler Service — DESIGN

## Responsibility
Run periodic refresh, KPI rollups, and notifications.

## API (MVP)
- POST /scheduler/run {goal_id|tenant_id}
- GET  /scheduler/status

## Data Ownership (Postgres)
Tables: job_run, job_metric

### Example Schema (SQLModel)
```python
from sqlmodel import SQLModel, Field, JSON
class TenantScoped(SQLModel):
    tenant_id: str = Field(index=True)

class Goal(SQLModel, table=True):
    id: str = Field(primary_key=True)
    tenant_id: str = Field(index=True)
    text: str
    goal_dsl: JSON | None = None
    status: str = "new"
```
## Sequences
- On create: validate JWT→OPA allow→persist→emit domain event→trace span.
- On read: enforce tenant scope, paginate, cache as needed.

## Non‑Functionals
- P50 read < 50ms, P95 < 200ms; idempotent POST with request keys.
- Tracing (OTel), metrics (Prometheus), logs (JSON).
- Security: Keycloak JWT, OPA checks, per‑tenant row scoping.
