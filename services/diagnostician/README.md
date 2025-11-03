# Diagnostician Service

Phase 3 stub that exposes `/v1/diagnose` via FastAPI. It emits canned relaxation suggestions to mimic infeasibility diagnostics.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.diagnostician.main:app --reload --port 8006
```

Sample request:

```bash
curl -X POST http://localhost:8006/v1/diagnose \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{"ops": {"metadata": {"problem_type": "inventory_planning"}}}'
```
