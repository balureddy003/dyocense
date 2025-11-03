# Compiler Service

Phase 2 compiler service exposing `/v1/compile` via FastAPI. The endpoint orchestrates knowledge retrieval, OptiGuide-style playbook hints, and LLM synthesis before falling back to deterministic stubs.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.compiler.main:app --reload --port 8001
```

Send a request:

```bash
curl -X POST http://localhost:8001/v1/compile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo-tenant" \
  -d '{"goal": "Plan inventory for widgets", "tenant_id": "demo", "project_id": "phase1"}'
```

### Offline evaluation

Use `scripts/evaluate_compiler.py examples/compiler_goals.jsonl` to run the compiler against a dataset and review success metrics plus captured telemetry under `artifacts/compiler_eval.json`.
