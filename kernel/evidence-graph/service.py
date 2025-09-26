"""Evidence Graph persistence using append-only JSON stores and hashing."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Mapping

from kernel.datamodel import (
    EvidenceRef,
    EvidenceSnapshot,
    ExplainabilityHints,
    OptiModel,
    ScenarioSet,
    Solution,
    optimodel_to_dict,
    scenario_set_to_dict,
    solution_to_dict,
)


class EvidenceGraphService:
    """Persists optimization traces as snapshots and graph relationships."""

    def __init__(
        self,
        data_root: Path | None = None,
        *,
        available: bool = True,
        max_snapshots: int = 200,
    ) -> None:
        self.data_root = data_root or Path(__file__).resolve().parent / "data"
        self.snapshot_dir = self.data_root / "snapshots"
        self.graph_log = self.data_root / "graph.jsonl"
        self.queue_file = self.data_root / "pending.jsonl"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.graph_log.parent.mkdir(parents=True, exist_ok=True)
        self.graph_log.touch(exist_ok=True)
        self.queue_file.touch(exist_ok=True)
        self.available = available
        self.last_status: Dict[str, Any] = {}
        self.max_snapshots = max_snapshots

    def persist(
        self,
        optimodel: OptiModel,
        solution: Solution,
        scenarios: ScenarioSet,
        hints: ExplainabilityHints,
        metadata: Mapping[str, Any] | None = None,
    ) -> EvidenceRef:
        snapshot = self._build_snapshot(optimodel, solution, scenarios, hints, metadata)
        snapshot_json = json.dumps(snapshot, sort_keys=True)
        snapshot_hash = hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()
        snapshot_path = self.snapshot_dir / f"{snapshot_hash}.json"
        if not snapshot_path.exists():
            snapshot_path.write_text(snapshot_json, encoding="utf-8")
            self._garbage_collect()

        event = self._build_graph_event(snapshot_hash, snapshot)
        if self.available:
            self._append_graph(event)
            self.last_status = {
                "queued": False,
                "snapshot_hash": snapshot_hash,
                "plan_id": snapshot["plan_id"],
            }
        else:
            self._enqueue_event(event)
            self.last_status = {
                "queued": True,
                "snapshot_hash": snapshot_hash,
                "plan_id": snapshot["plan_id"],
            }
        return EvidenceRef(uri=f"evidence://{snapshot_hash}", snapshot_hash=snapshot_hash)

    def _build_snapshot(
        self,
        optimodel: OptiModel,
        solution: Solution,
        scenarios: ScenarioSet,
        hints: ExplainabilityHints,
        metadata: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        plan_id = str((metadata or {}).get("run_id") or uuid.uuid4())
        evidence = EvidenceSnapshot(
            plan_id=plan_id,
            optimodel=optimodel,
            solution=solution,
            scenarios=scenarios,
            hints=hints,
        )
        payload = asdict(evidence)
        payload["metadata"] = self._redact_metadata(metadata)
        payload["timestamp"] = time.time()
        payload["optimodel"] = optimodel_to_dict(optimodel)
        payload["solution"] = solution_to_dict(solution)
        payload["scenarios"] = scenario_set_to_dict(scenarios)
        payload["hints"] = asdict(hints)
        return payload

    def _build_graph_event(self, snapshot_hash: str, snapshot: Mapping[str, Any]) -> Dict[str, Any]:
        solution = snapshot["solution"]
        hint_track = snapshot["hints"].get("track", [])
        plan_id = snapshot["plan_id"]
        node_plan = {
            "id": plan_id,
            "type": "Plan",
            "kpis": solution.get("kpis", {}),
        }
        node_solver = {
            "id": f"solve_{snapshot_hash}",
            "type": "SolverRun",
            "status": solution.get("status", "UNKNOWN"),
            "gap": solution.get("gap", 0.0),
        }
        nodes: List[Dict[str, Any]] = [node_plan, node_solver]
        edges: List[Dict[str, Any]] = [
            {"type": "EXECUTED_AS", "from": node_plan["id"], "to": node_solver["id"]},
        ]

        binding_constraints = solution.get("binding_constraints", [])
        for constraint in binding_constraints:
            nodes.append({"id": f"constraint::{constraint}", "type": "Constraint", "name": constraint})
            edges.append(
                {
                    "type": "BOUND_BY",
                    "from": node_solver["id"],
                    "to": f"constraint::{constraint}",
                }
            )

        for track in hint_track:
            nodes.append({"id": f"hint::{track}", "type": "Hint", "name": track})
            edges.append(
                {
                    "type": "TRACKS",
                    "from": node_plan["id"],
                    "to": f"hint::{track}",
                }
            )

        objective_terms = snapshot["optimodel"].get("objective_terms", [])
        for term in objective_terms:
            obj_id = f"objective::{term['name']}"
            nodes.append({"id": obj_id, "type": "Objective", "weight": term.get("weight")})
            edges.append({"type": "OPTIMIZES", "from": node_plan["id"], "to": obj_id})

        step_nodes: List[Dict[str, Any]] = []
        for idx, step in enumerate(solution.get("steps", [])):
            step_id = f"step::{idx}"
            step_node = {
                "id": step_id,
                "type": "Step",
                "sku": step["sku"],
                "supplier": step["supplier"],
                "period": step["period"],
                "quantity": step["quantity"],
                "price": step.get("price"),
            }
            nodes.append(step_node)
            step_nodes.append(step_node)
            edges.append({"type": "PRODUCES", "from": node_solver["id"], "to": step_id})
            for constraint in binding_constraints:
                edges.append({"type": "IMPACTED_BY", "from": step_id, "to": f"constraint::{constraint}"})
            for term in objective_terms:
                edges.append({"type": "CONTRIBUTES_TO", "from": step_id, "to": f"objective::{term['name']}"})

        data_sources = [
            {
                "id": f"datasource::scenario::{scenario_id}",
                "type": "DataSource",
                "scenario_id": scenario_id,
            }
            for scenario_id in snapshot.get("metadata", {}).get("scenario_ids", [])
        ]
        for ds_node in data_sources:
            nodes.append(ds_node)
            for step_node in step_nodes:
                edges.append({"type": "DERIVED_FROM", "from": step_node["id"], "to": ds_node["id"]})
            for term in objective_terms:
                edges.append({"type": "SUPPORTS", "from": ds_node["id"], "to": f"objective::{term['name']}"})

        return {
            "snapshot": snapshot_hash,
            "plan_id": plan_id,
            "timestamp": snapshot["timestamp"],
            "nodes": nodes,
            "edges": edges,
            "kpis": solution.get("kpis", {}),
            "binding_constraints": binding_constraints,
        }

    def _append_graph(self, event: Mapping[str, Any]) -> None:
        with self.graph_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")

    def _enqueue_event(self, event: Mapping[str, Any]) -> None:
        with self.queue_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")

    def _garbage_collect(self) -> None:
        snapshots = sorted(self.snapshot_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        if len(snapshots) <= self.max_snapshots:
            return
        for path in snapshots[: len(snapshots) - self.max_snapshots]:
            path.unlink(missing_ok=True)

    def _redact_metadata(self, metadata: Mapping[str, Any] | None) -> Dict[str, Any]:
        redacted: Dict[str, Any] = {}
        if not metadata:
            return redacted
        for key, value in metadata.items():
            if any(token in key.lower() for token in {"email", "phone", "ssn"}):
                continue
            redacted[key] = value
        return redacted

    def query_supplier_explanation(self, plan_id: str, supplier_id: str) -> Dict[str, Any]:
        """Return explanation path and counterfactuals for a supplier in a plan."""

        events = self._load_events(plan_id)
        if not events:
            raise ValueError(f"No evidence found for plan_id={plan_id}")
        event = events[-1]
        snapshot_hash = event["snapshot"]
        snapshot_path = self.snapshot_dir / f"{snapshot_hash}.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

        adjacency: Dict[str, List[str]] = {}
        for edge in event.get("edges", []):
            adjacency.setdefault(edge["from"], []).append(edge["to"])

        step_nodes = [
            node
            for node in event.get("nodes", [])
            if node.get("type") == "Step" and node.get("supplier") == supplier_id
        ]
        if not step_nodes:
            raise ValueError(f"Supplier {supplier_id} not found for plan {plan_id}")
        step_node = step_nodes[0]

        path = self._build_explanation_path(step_node["id"], adjacency)
        counterfactual = self._counterfactual_alternative(step_node, snapshot)

        return {
            "plan_id": plan_id,
            "supplier": supplier_id,
            "path": path,
            "counterfactual": counterfactual,
        }

    def _load_events(self, plan_id: str) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        with self.graph_log.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = json.loads(line)
                if event.get("plan_id") == plan_id:
                    events.append(event)
        return events

    def _build_explanation_path(
        self,
        step_id: str,
        adjacency: Mapping[str, List[str]],
    ) -> List[str]:
        visited = set()
        path: List[str] = [step_id]
        frontier = [step_id]
        while frontier:
            next_frontier: List[str] = []
            for node in frontier:
                if node in visited:
                    continue
                visited.add(node)
                for neighbor in adjacency.get(node, []):
                    path.append(neighbor)
                    next_frontier.append(neighbor)
            frontier = next_frontier
        return path

    def _counterfactual_alternative(
        self,
        step_node: Mapping[str, Any],
        snapshot: Mapping[str, Any],
    ) -> Dict[str, Any]:
        sku = step_node.get("sku")
        current_supplier = step_node.get("supplier")
        metadata = snapshot.get("metadata", {})
        prices = metadata.get("compiled_inputs", {}).get("prices", {})
        sku_prices = prices.get(sku, {}) if isinstance(prices, dict) else {}
        alternatives = {
            supplier: price
            for supplier, price in sku_prices.items()
            if supplier != current_supplier
        }
        if not alternatives:
            return {"available": False, "message": "No alternative suppliers"}
        alternative_supplier, price = min(alternatives.items(), key=lambda item: item[1])
        return {
            "available": True,
            "alternative_supplier": alternative_supplier,
            "price": price,
            "quantity": step_node.get("quantity"),
        }
