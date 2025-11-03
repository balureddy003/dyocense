# Scenario Service

Phase 3 service that manages what-if scenarios on top of compiled goals.

## Features
- Create scenarios by cloning a baseline version and applying data/parameter overrides.
- Optionally re-run the compiler pipeline (Phase 2) with overrides before storing a new version.
- Diff parameters between baseline and scenario for quick inspection.
- Expose REST endpoints to list and fetch scenarios tied to a project.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.scenario.main:app --reload --port 8087
```

Create a scenario:

```bash
curl -X POST http://localhost:8087/v1/scenarios \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{
        "base_version_id": "ver-abc123",
        "label": "Demand spike",
        "parameter_overrides": {"demand": {"widget": 175}},
        "recompute": false
      }'
```
