# Dyocense Python SDK (Stub)

This SDK wraps the Phase 4/5 services (compile, forecast, policy, optimise, diagnose, explain, evidence) behind a simple Python client. It is currently a thin wrapper over the REST endpoints and will evolve once the services stabilise.

## Install (local development)

```bash
pip install -e packages/sdk-python
```

## Example

```python
from dyocense_sdk.client import DyocenseClient

client = DyocenseClient(token="demo-tenant")
result = client.run_decision_flow(goal="Reduce holding cost")
print(result.explanation["summary"])

# Or run via the orchestration API
run = client.submit_run(goal="Reduce holding cost")
status = client.get_run(run["run_id"])
print(status["status"])
```

The `run_decision_flow` helper orchestrates compile → forecast → policy → optimise → diagnose → explain → evidence logging. All methods accept overrides and return typed dataclasses for easy use in applications.
