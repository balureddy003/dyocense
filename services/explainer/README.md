# Explainer Service

Phase 2 stub that exposes `/v1/explain` via FastAPI. It generates templated summaries for SolutionPack outputs and optional forecasts.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.explainer.main:app --reload --port 8004
```

Sample request (assuming optimiser output saved to `solution.json`):

```bash
curl -X POST http://localhost:8004/v1/explain \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{"goal": "Reduce holding cost", "solution": {}}'
```
