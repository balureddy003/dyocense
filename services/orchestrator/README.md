# Orchestrator Service

Provides a single `/v1/runs` endpoint that executes the full Dyocense decision pipeline (compile → forecast → policy → optimise → diagnose → explain → evidence). Runs execute in the background and can be polled via `GET /v1/runs/{run_id}`.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.orchestrator.main:app --reload --port 8010
```

Submit a run:

```bash
curl -X POST http://localhost:8010/v1/runs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{"goal": "Reduce holding cost"}'
```

Poll status:

```bash
curl -H "Authorization: Bearer demo-tenant" http://localhost:8010/v1/runs/<run_id>
```
