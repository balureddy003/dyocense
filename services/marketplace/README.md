# Marketplace Service

Phase 5 stub providing a `/v1/catalog` endpoint that returns archetypes/solvers/connectors available to SDKs and agent integrations.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.marketplace.main:app --reload --port 8008
```

Sample request:

```bash
curl -X GET http://localhost:8008/v1/catalog \
  -H "Authorization: Bearer demo-tenant"
```
