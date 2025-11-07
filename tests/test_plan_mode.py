from __future__ import annotations

import time
from pathlib import Path
from typing import Dict

import httpx
from fastapi.testclient import TestClient

from services.kernel.main import app as kernel_app

client = TestClient(kernel_app)


def test_planner_create_and_execute_basic_plan():
    # Create a plan
    resp = client.post(
        "/v1/plan",
        json={
            "goal": "Reduce stockouts while minimising holding cost",
            "template_id": "inventory_basic",
            "horizon": 2,
            "series": [
                {"name": "sku_A", "values": [10, 12, 15]},
                {"name": "sku_B", "values": [5, 6, 7]},
            ],
        },
    )
    assert resp.status_code == 200
    plan_body = resp.json()
    plan_id = plan_body["plan_id"]
    assert plan_body["status"] == "draft"
    assert plan_body["plan"]["steps"], "Steps should be populated in draft plan"

    # Execute the plan
    exec_resp = client.post(f"/v1/plan/execute/{plan_id}")
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "executing"

    # Poll for completion
    for _ in range(40):  # up to ~8s (0.2 * 40)
        get_resp = client.get(f"/v1/plan/{plan_id}")
        assert get_resp.status_code == 200
        status = get_resp.json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(0.2)
    assert status == "completed", f"Plan did not complete, final status={status}"  # noqa: F821

    # Artifacts should exist
    artifacts_dir = Path("artifacts/plans") / plan_id
    assert artifacts_dir.exists(), "Artifacts directory missing"
    expected = {"forecast.json", "policy.json", "solution.json", "diagnostics.json", "explanation.json", "evidence.json", "plan.json"}
    present = {p.name for p in artifacts_dir.glob("*.json")}
    missing = expected - present
    assert not missing, f"Missing artifacts: {missing}"  # noqa: F821

    # Trace file should exist (tracing enabled by default via env default)
    trace_file = artifacts_dir / "trace.jsonl"
    assert trace_file.exists(), "Trace file missing"
    lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
    assert any("step.start" in l for l in lines), "Trace should contain step.start events"
    assert any("step.end" in l for l in lines), "Trace should contain step.end events"
    assert any("plan.end" in l for l in lines), "Trace should contain plan.end event"


def test_orchestrator_run_plan_mode():
    # Override auth dependency to bypass JWT validation for test
    from packages.kernel_common.deps import require_auth
    kernel_app.dependency_overrides[require_auth] = lambda: {"tenant_id": "demo-tenant", "subject": "tester"}
    run_resp = client.post(
        "/v1/runs",
        json={
            "goal": "Increase service level",
            "template_id": "inventory_basic",
            "horizon": 2,
            "mode": "plan",
        },
        headers={"Authorization": "Bearer ignored"},
    )
    assert run_resp.status_code == 202
    run_id = run_resp.json()["run_id"]

    # Poll for completion
    for _ in range(40):
        status_resp = client.get(f"/v1/runs/{run_id}")
        assert status_resp.status_code == 200
        status = status_resp.json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(0.2)
    assert status == "completed", f"Run did not complete, final status={status}"  # noqa: F821

    # Result bundle should contain plan and artifacts
    bundle: Dict = status_resp.json().get("result") or {}
    assert "plan" in bundle, "Plan missing from result bundle"
    assert "artifacts" in bundle, "Artifacts missing from result bundle"
    assert bundle["plan"]["status"] == "completed"

    # Ensure at least the solution artifact is present
    artifact_names = {a.get("name") for a in bundle["artifacts"]}
    assert "solution.json" in artifact_names, f"solution.json missing in artifacts {artifact_names}"  # noqa: F821
