#!/usr/bin/env python3
"""Benchmark compiler retrieval latency against a large dataset."""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import time
from typing import Dict, Iterable, List

from packages.knowledge import KnowledgeClient, KnowledgeDocument
from services.compiler.main import build_ops_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark compiler retrieval with a goal dataset.")
    parser.add_argument("dataset", type=pathlib.Path, help="JSONL file with documents to ingest.")
    parser.add_argument(
        "--goals",
        type=pathlib.Path,
        default=None,
        help="Optional JSON file containing an array of goal strings to evaluate."
    )
    parser.add_argument("--tenant-id", default="demo-tenant")
    parser.add_argument("--project-id", default="benchmark-project")
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("artifacts/compiler_benchmark.json"))
    return parser.parse_args()


def load_documents(path: pathlib.Path) -> Iterable[KnowledgeDocument]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            yield KnowledgeDocument(
                tenant_id=payload.get("tenant_id"),
                project_id=payload.get("project_id"),
                collection=payload.get("collection", "ops_context"),
                document_id=payload.get("document_id"),
                text=payload.get("text", ""),
                metadata=payload.get("metadata", {}),
            )


def load_goals(path: pathlib.Path | None) -> List[str]:
    if path is None:
        return [
            "Optimise inventory levels for seasonal products",
            "Design staffing rota for weekend sales",
            "Plan energy storage dispatch for peak shaving",
        ]
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return [str(item) for item in data]
    raise ValueError("Goal file must contain a JSON array")


def benchmark(goals: List[str], tenant_id: str, project_id: str) -> Dict[str, object]:
    durations: List[float] = []
    snippet_counts: List[int] = []
    outputs: List[Dict[str, object]] = []

    for goal in goals:
        start = time.perf_counter()
        ops, goal_pack = build_ops_document(goal, tenant_id, project_id)
        end = time.perf_counter()
        provenance = goal_pack.get("provenance", {})
        retrieval = goal_pack.get("retrieval", {})
        duration = provenance.get("duration_seconds", end - start)
        durations.append(duration)
        snippet_counts.append(retrieval.get("snippet_count", 0))
        outputs.append(
            {
                "goal": goal,
                "version_id": goal_pack.get("version_id"),
                "duration_seconds": duration,
                "snippet_count": retrieval.get("snippet_count", 0),
                "compiler_source": provenance.get("compiler_source"),
            }
        )

    summary = {
        "total_runs": len(goals),
        "avg_duration_seconds": statistics.fmean(durations) if durations else 0.0,
        "p95_duration_seconds": _percentile(durations, 95),
        "avg_snippet_count": statistics.fmean(snippet_counts) if snippet_counts else 0.0,
        "outputs": outputs,
    }
    return summary


def _percentile(values: List[float], percentile: int) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * percentile / 100
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[int(k)]
    d0 = sorted_values[f] * (c - k)
    d1 = sorted_values[c] * (k - f)
    return d0 + d1


def main() -> None:
    args = parse_args()
    client = KnowledgeClient()

    documents = list(load_documents(args.dataset))
    client.batch_ingest(documents)

    goals = load_goals(args.goals)
    results = benchmark(goals, args.tenant_id, args.project_id)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
