# Policy Service — DESIGN

## Responsibility
Manage tenant-specific policy bundles (OPA rules + thresholds), provide versioning/change review, and surface audit history of Policy Guard decisions.

## API (MVP)
- `POST /policies` — create policy with initial draft version
- `POST /policies/{id}/versions` — submit updated draft version
- `POST /policies/{id}/activate` — promote version to active (captures activation note)
- `POST /policies/{id}/thresholds` — self-service threshold update (creates new version)
- `GET /policies` — list policies for tenant
- `GET /policies/{id}/versions/{version_id}` — fetch version detail
- `GET /audits` — view policy decisions recorded from Policy Guard / Evidence Graph

## Data Ownership (MongoDB)
Collections: `policies`, `policy_audits`

```json
{
  "tenant_id": "tenant_demo",
  "policy_id": "pol_123",
  "active_version_id": "ver_002",
  "versions": [
    {
      "version_id": "ver_001",
      "name": "Budget Policy",
      "description": "Controls monthly budget",
      "rules": [{"name": "budget_cap", "definition": {"max_budget": 10000}}],
      "thresholds": {"scenario_cap": 50},
      "status": "active",
      "created_at": "2025-01-01T10:00:00Z",
      "created_by": "ops@tenant",
      "activated_at": "2025-01-02T09:00:00Z"
    }
  ],
  "updated_at": "2025-01-02T09:00:00Z"
}
```

```json
{
  "audit_id": "audit_456",
  "tenant_id": "tenant_demo",
  "policy_id": "pol_123",
  "version_id": "ver_002",
  "decision": {
    "allow": true,
    "policy_snapshot": {"allow": true, "controls": {"scenario_cap": 80}}
  },
  "source": "policy_guard",
  "created_at": "2025-01-05T08:30:00Z"
}
```

## Sequences
- **Versioning**: create draft -> review -> activate (stores who/when); thresholds update produces new draft with unchanged rules.
- **Audit**: Evidence/Policy Guard sends decisions (`log_audit`) so users can inspect past allow/deny rationale.
- **Controls Sync**: Plan/Scheduler services read thresholds via Policy Guard snapshot; this service lets tenants self-serve updates.

## Non-Functionals
- Track full version history, activation metadata, and audit trail.
- Tenant isolation enforced by query filters.
- Reuse Mongo indexes for fast lookups; surface change events to downstream services (future).
