# Kernel API Service

Unified FastAPI entrypoint that aggregates all Decision Kernel routes (compile, forecast, policy, optimise, diagnose, explain, evidence, marketplace). Deploy this service when you want a single port without running each microservice independently.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001
```

All existing SDKs default to the individual service ports. To target the unified kernel, override the `service_urls` map in the SDKs so that each service points to `http://localhost:8001`.
