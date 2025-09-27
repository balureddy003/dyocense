from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from api.modules.evidence.app import app, get_repository
from api.modules.evidence.storage import EvidenceRepository

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def client() -> TestClient:
    mongo_client = mongomock.MongoClient()
    collection = mongo_client["unit-test"]["evidence"]
    repository = EvidenceRepository(collection)

    app.dependency_overrides[get_repository] = lambda: repository

    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        yield test_client

    app.dependency_overrides.clear()


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer tenant_demo"}


def test_evidence_endpoints(client: TestClient) -> None:
    repository: EvidenceRepository = client.repository  # type: ignore[attr-defined]
    now = datetime.now(timezone.utc)
    repository.upsert_snapshot(
        tenant_id="tenant_demo",
        evidence_ref="evidence://abc",
        snapshot={
            "solution": {
                "status": "FEASIBLE",
                "kpis": {"cost": 100},
                "steps": [
                    {"sku": "SKU1", "supplier": "SUP1", "period": "t1", "quantity": 10, "price": 10.0}
                ],
            },
            "diagnostics": {"simulation": {"mean_service": 0.95}},
            "policy": {"allow": True, "policy_id": "policy.guard.v1"},
            "scenarios": {"scenarios": [{"id": 0, "demand": {"SKU1": {"t1": 10}}, "lead_time_days": {"SKU1": 2}}]},
        },
        plan_id="plan_1",
        goal_id="goal_1",
    )

    list_resp = client.get("/evidence", headers=_auth_headers())
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    detail_resp = client.get("/evidence/evidence://abc", headers=_auth_headers())
    assert detail_resp.status_code == 200
    detail_payload = detail_resp.json()
    assert detail_payload["plan_id"] == "plan_1"

    supplier_resp = client.get("/evidence/evidence://abc/suppliers/SUP1", headers=_auth_headers())
    assert supplier_resp.status_code == 200
    assert supplier_resp.json()["supplier_id"] == "SUP1"

    constraint_resp = client.get("/evidence/evidence://abc/constraints/budget", headers=_auth_headers())
    assert constraint_resp.status_code == 200

    scenario_resp = client.get("/evidence/evidence://abc/scenarios/0", headers=_auth_headers())
    assert scenario_resp.status_code == 200

    share_resp = client.post(
        "/evidence/evidence://abc/share",
        json={"expires_in_minutes": 10},
        headers=_auth_headers(),
    )
    assert share_resp.status_code == 200
    share_id = share_resp.json()["share_id"]

    open_resp = client.get(f"/share/{share_id}")
    assert open_resp.status_code == 200
    assert open_resp.json()["redacted"]
