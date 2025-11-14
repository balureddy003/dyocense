from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

import requests

API = os.getenv("API_BASE_URL", "http://localhost:8001")

SAMPLE = {
    "goal": "Reduce excess inventory for seasonal items",
    "template_id": "inventory_optimization",
    "horizon": 3
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=API)
    args = parser.parse_args()

    # Create plan
    r = requests.post(f"{args.api}/v1/plan", json=SAMPLE)
    r.raise_for_status()
    plan_id = r.json()["plan_id"]

    # Execute plan
    r = requests.post(f"{args.api}/v1/plan/execute/{plan_id}")
    r.raise_for_status()

    # Poll
    for _ in range(60):
        time.sleep(0.5)
        s = requests.get(f"{args.api}/v1/plan/{plan_id}").json()
        if s["status"] in ("completed", "failed"): break

    # Load artifacts
    plan_dir = Path("artifacts/plans") / plan_id
    result = {
        "status": s["status"],
        "risks": s.get("risks", []),
        "has_solution": (plan_dir / "solution.json").exists(),
        "has_forecast": (plan_dir / "forecast.json").exists(),
        "trace_lines": (plan_dir / "trace.jsonl").read_text().count("\n") if (plan_dir / "trace.jsonl").exists() else 0,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
