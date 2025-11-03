# Optimiser Service

Optimiser service exposing `/v1/optimise` via FastAPI. It uses OR-Tools CBC mixed integer programming when available (install `ortools` via `requirements-dev.txt`), falling back to the earlier deterministic solver if the dependency is missing.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.optimiser.main:app --reload --port 8002
```

Sample request (using compiler output):

```bash
curl -X POST http://localhost:8002/v1/optimise \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d @examples/inventory_simple.ops.json
```
