from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.modules.scheduler.app import app, get_repository
from api.modules.scheduler.storage import SchedulerRepository

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def client() -> TestClient:
    mongo_client = mongomock.MongoClient()
    jobs = mongo_client["unit-test"]["jobs"]
    tenants = mongo_client["unit-test"]["tenants"]
    repository = SchedulerRepository(jobs, tenants)

    app.dependency_overrides[get_repository] = lambda: repository

    with TestClient(app) as test_client:
        test_client.repository = repository  # type: ignore[attr-defined]
        yield test_client

    app.dependency_overrides.clear()


def _headers() -> dict[str, str]:
    return {"Authorization": "Bearer tenant_demo"}


def test_enqueue_and_lease(client: TestClient) -> None:
    enqueue_resp = client.post(
        "/queue/enqueue",
        json={
            "tenant_id": "tenant_demo",
            "tier": "pro",
            "payload": {"goaldsl": {"objective": {"cost": 1.0}}},
            "cost_estimate": {"solver_sec": 2.0},
        },
        headers=_headers(),
    )
    assert enqueue_resp.status_code == 200
    job_id = enqueue_resp.json()["job_id"]

    lease_resp = client.post(
        "/queue/lease",
        json={"worker_id": "worker-1", "max_jobs": 1},
        headers=_headers(),
    )
    assert lease_resp.status_code == 200
    jobs = lease_resp.json()["jobs"]
    assert len(jobs) == 1 and jobs[0]["job_id"] == job_id

    heartbeat_resp = client.post(
        f"/queue/{job_id}/heartbeat",
        json={"worker_id": "worker-1", "lease_extension_seconds": 120},
        headers=_headers(),
    )
    assert heartbeat_resp.status_code == 200

    complete_resp = client.post(
        f"/queue/{job_id}/complete",
        json={"worker_id": "worker-1", "result": {"status": "done"}},
        headers=_headers(),
    )
    assert complete_resp.status_code == 200

    budget_resp = client.get("/tenants/tenant_demo/budget", headers=_headers())
    assert budget_resp.status_code == 200
