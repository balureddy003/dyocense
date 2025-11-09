# Kernel API Service

Unified FastAPI entrypoint that aggregates all Decision Kernel routes (compile, forecast, policy, optimise, diagnose, explain, evidence, marketplace). Deploy this service when you want a single port without running each microservice independently.

## Run locally

```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001
```

NOTE: For reliable FastAPI / Pydantic behavior use Python 3.11 for the virtualenv. Python 3.13 has known compatibility issues with older pydantic/fastapi stacks used in this repo. Create a Python 3.11 venv and install the requirements before running.

Example:

```bash
# using pyenv or system Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r services/kernel/requirements.txt
PYTHONPATH=. uvicorn services.kernel.main:app --reload --port 8001
```

All existing SDKs default to the individual service ports. To target the unified kernel, override the `service_urls` map in the SDKs so that each service points to `http://localhost:8001`.

## SMB onboarding helpers

The kernel now exposes lightweight endpoints that power the SMB shell:

- `POST /v1/onboarding/{tenant_id}` — provisions a sample workspace + plan using the `OnboardingRequest` body defined in `packages/contracts/openapi/decision-kernel.yaml`. The response includes `workspace` and `plan` objects that conform to the shared `workspace.schema.json` and `plan.schema.json`.
- `GET /v1/tenants/{tenant_id}/plans` — returns the latest plans for a tenant. Responses follow the `PlanListResponse` contract so the UI can hydrate Planner without relying on `localStorage`.

Update clients to pull these schemas from `packages/contracts/schemas` rather than duplicating inline types.
