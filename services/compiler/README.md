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

### Retrieval benchmarking

To benchmark compilation with a larger retrieval corpus, ingest `examples/datasets/goal_context_large.jsonl` and run:

```bash
KNOWLEDGE_BACKEND=qdrant scripts/benchmark_compiler_retrieval.py examples/datasets/goal_context_large.jsonl \
  --tenant-id demo-tenant --project-id benchmark-run
```

Results, including average latency and snippet counts, are written to `artifacts/compiler_benchmark.json`.

## LLM providers

Configure the compiler by setting `LLM_PROVIDER` and the provider-specific environment variables:

| Provider | Required variables |
| --- | --- |
| `ollama` (default) | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, optional `OLLAMA_TIMEOUT`, `OLLAMA_STREAM` |
| `openai` | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| `azure` | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT`, optional `AZURE_OPENAI_TEMPERATURE`, `AZURE_OPENAI_MAX_TOKENS` |
