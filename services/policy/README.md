# Policy Service

Phase 3 stub that exposes `/v1/policy/evaluate` via FastAPI. It simulates OPA/Rego checks and always returns an "allow" verdict with explanatory messages.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.policy.main:app --reload --port 8005
```

Sample request:

```bash
curl -X POST http://localhost:8005/v1/policy/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{"tenant_id": "demo", "ops": {"metadata": {"problem_type": "inventory_planning"}}}'
```
