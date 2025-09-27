from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.modules.policy.app import app, get_repository
from api.modules.policy.storage import PolicyRepository

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def client() -> TestClient:
    mongo_client = mongomock.MongoClient()
    policies = mongo_client["unit-test"]["policies"]
    audits = mongo_client["unit-test"]["audits"]
    repository = PolicyRepository(policies, audits)

    app.dependency_overrides[get_repository] = lambda: repository

    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        yield test_client

    app.dependency_overrides.clear()


def _headers() -> dict[str, str]:
    return {"Authorization": "Bearer tenant_demo"}


def test_policy_workflow(client: TestClient) -> None:
    create_resp = client.post(
        "/policies",
        json={
            "name": "Budget Policy",
            "description": "Controls budget caps",
            "rules": [{"name": "budget_cap", "definition": {"max_budget": 10000}}],
            "thresholds": {"scenario_cap": 50},
        },
        headers=_headers(),
    )
    assert create_resp.status_code == 201
    created_payload = create_resp.json()
    version_id = created_payload["version_id"]

    policy_id = client.get("/policies", headers=_headers()).json()[0]["policy_id"]
    activate_resp = client.post(
        f"/policies/{policy_id}/activate",
        json={"version_id": version_id},
        headers=_headers(),
    )
    assert activate_resp.status_code == 200

    thresholds_resp = client.post(
        f"/policies/{policy_id}/thresholds",
        json={"thresholds": {"scenario_cap": 80}},
        headers=_headers(),
    )
    assert thresholds_resp.status_code == 200
    latest_version_id = thresholds_resp.json()["version_id"]

    version_resp = client.get(
        f"/policies/{policy_id}/versions/{latest_version_id}",
        headers=_headers(),
    )
    assert version_resp.status_code == 200
    version_payload = version_resp.json()
    assert version_payload["thresholds"]["scenario_cap"] == 80
    assert len(version_payload["rules"]) == len(created_payload.get("rules", []))

    audits_resp = client.get("/audits", headers=_headers())
    assert audits_resp.status_code == 200
