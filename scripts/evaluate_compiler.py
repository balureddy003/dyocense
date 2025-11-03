#!/usr/bin/env python3
"""
Offline evaluation harness for the compiler pipeline (Phase 2).

Pass a JSON Lines file containing records with at least a `goal` field and optional
`tenant_id`, `project_id`, and `data_inputs`. The script executes the compiler flow
for each record and reports success/failure metrics along with captured telemetry.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List

from services.compiler.main import build_ops_document, telemetry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate compiler outputs offline.")
    parser.add_argument("dataset", type=pathlib.Path, help="JSONL dataset with compiler test goals.")
    parser.add_argument("--tenant-id", default="demo-tenant")
    parser.add_argument("--project-id", default="eval-run")
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("artifacts/compiler_eval.json"))
    return parser.parse_args()


def load_records(path: pathlib.Path) -> List[Dict]:
    records: List[Dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            records.append(json.loads(line))
    return records


def evaluate(records: List[Dict], tenant_id: str, project_id: str) -> Dict[str, object]:
    successes = 0
    outputs: List[Dict] = []
    telemetry.events.clear()

    for idx, record in enumerate(records, start=1):
        goal = record.get("goal")
        data_inputs = record.get("data_inputs")
        ops, goal_pack = build_ops_document(goal, tenant_id, f"{project_id}-{idx}", data_inputs=data_inputs)
        ok = _has_required_sections(ops)
        if ok:
            successes += 1
        outputs.append({
            "goal": goal,
            "success": ok,
            "version_id": goal_pack.get("version_id"),
            "ops": ops,
            "goal_pack": goal_pack,
        })
    return {
        "total": len(records),
        "successes": successes,
        "success_rate": successes / len(records) if records else 0.0,
        "outputs": outputs,
        "telemetry": telemetry.events,
    }


def _has_required_sections(ops: Dict) -> bool:
    required = ["objective", "decision_variables", "parameters", "constraints", "kpis"]
    return all(section in ops for section in required)


def main() -> None:
    args = parse_args()
    records = load_records(args.dataset)
    results = evaluate(records, args.tenant_id, args.project_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
