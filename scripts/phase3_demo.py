#!/usr/bin/env python3
"""Run the Dyocense orchestration pipeline end-to-end using the in-process kernel."""

from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from services.kernel.main import app as kernel_app


def run_demo() -> dict:
    client = TestClient(kernel_app)
    headers = {"Authorization": "Bearer demo-tenant"}

    submit = client.post(
        "/v1/runs",
        json={"goal": "Minimise holding cost", "project_id": "demo-run"},
        headers=headers,
    )
    submit.raise_for_status()
    run_id = submit.json()["run_id"]

    payload = {}
    for _ in range(12):
        status = client.get(f"/v1/runs/{run_id}", headers=headers)
        status.raise_for_status()
        payload = status.json()
        if payload["status"] in {"completed", "failed"}:
            break
        time.sleep(0.1)

    if payload.get("status") != "completed":
        raise RuntimeError(f"Run {run_id} failed: {payload.get('error')}")

    return payload["result"]


def main() -> None:
    result = run_demo()
    Path("phase3_demo_output.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("Demo artefact written to phase3_demo_output.json")


if __name__ == "__main__":
    main()
