from pathlib import Path

from fastapi.testclient import TestClient

from services.kernel.main import app as kernel_app


def test_orchestrator_run_completes():
    client = TestClient(kernel_app)
    headers = {"Authorization": "Bearer demo-tenant"}

    submit = client.post(
        "/v1/runs",
        json={
            "goal": "Maximise revenue",
            "archetype_id": "inventory_basic",
            "project_id": "test-run",
            "data_inputs": {
                "demand": [{"sku": "widget", "quantity": 120}, {"sku": "gadget", "quantity": 95}],
                "holding_cost": [{"sku": "widget", "cost": 2.5}, {"sku": "gadget", "cost": 1.75}]
            }
        },
        headers=headers,
    )
    assert submit.status_code == 202
    run_id = submit.json()["run_id"]

    for _ in range(10):
        status = client.get(f"/v1/runs/{run_id}", headers=headers)
        assert status.status_code == 200
        payload = status.json()
        if payload["status"] in {"completed", "failed"}:
            break
    assert payload["status"] == "completed"
    assert payload["archetype_id"] == "inventory_basic"
    assert payload["result"]["solution"]["metadata"]["solver"] in {"stub-optimiser", "cbc-mip"}

    artifacts = payload["result"].get("artifacts", {})
    solution_artifact = artifacts.get("solution_pack", {})
    solution_path = Path(solution_artifact["path"])
    assert solution_path.exists()

    # Cleanup artifacts created by the test run
    run_dir = solution_path.parent
    for file in run_dir.glob("*.json"):
        file.unlink(missing_ok=True)
    run_dir.rmdir()
