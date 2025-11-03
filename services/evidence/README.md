# Evidence Service

Phase 3 stub that stores OPS, SolutionPack, and Explanation payloads in MongoDB (or an in-memory fallback when MongoDB is unavailable).

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.evidence.main:app --reload --port 8007
```

Sample request (assuming artefacts saved to JSON files):

```bash
curl -X POST http://localhost:8007/v1/evidence/log \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{"run_id": "demo-run", "tenant_id": "demo", "ops": {}, "solution": {}, "explanation": {}}'
```
