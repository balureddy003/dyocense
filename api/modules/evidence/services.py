"""High level evidence query services."""
from __future__ import annotations

from typing import Dict, List, Optional

from api.common import dto

from .storage import EvidenceRecord, EvidenceRepository


class EvidenceService:
    def __init__(self, repository: EvidenceRepository) -> None:
        self._repository = repository

    def list_evidence(self, tenant_id: str) -> List[EvidenceRecord]:
        return list(self._repository.list(tenant_id))

    def get_evidence(self, tenant_id: str, evidence_ref: str) -> Optional[EvidenceRecord]:
        return self._repository.get(tenant_id, evidence_ref)

    def list_supplier_steps(self, record: EvidenceRecord, supplier_id: str) -> List[Dict[str, object]]:
        solution = record.snapshot.get("solution", {})
        steps = solution.get("steps", []) if isinstance(solution, dict) else []
        return [step for step in steps if step.get("supplier") == supplier_id]

    def extract_policy_snapshot(self, record: EvidenceRecord) -> Optional[Dict[str, object]]:
        snapshot = record.snapshot.get("policy")
        if isinstance(snapshot, dict):
            return snapshot
        metadata = record.snapshot.get("metadata", {})
        if isinstance(metadata, dict):
            policy = metadata.get("policy_snapshot")
            if isinstance(policy, dict):
                return policy
        return None

    def supplier_explanation(self, record: EvidenceRecord, supplier_id: str) -> Dict[str, object]:
        path = []
        solution = record.snapshot.get("solution", {})
        diagnostics = record.snapshot.get("diagnostics", {})
        steps = solution.get("steps", []) if isinstance(solution, dict) else []
        for idx, step in enumerate(steps):
            if step.get("supplier") == supplier_id:
                path.append(f"step::{idx}")
        alternative = record.snapshot.get("metadata", {}).get("counterfactual") if isinstance(record.snapshot.get("metadata"), dict) else None
        return {
            "evidence_ref": record.evidence_ref,
            "supplier_id": supplier_id,
            "path": path,
            "alternative": alternative,
            "diagnostics": diagnostics,
        }

    def constraint_lineage(self, record: EvidenceRecord, constraint: str) -> Dict[str, object]:
        metadata = record.snapshot.get("metadata", {})
        graph = metadata.get("graph_event") if isinstance(metadata, dict) else None
        if not isinstance(graph, dict):
            return {"evidence_ref": record.evidence_ref, "constraint": constraint, "nodes": [], "edges": []}
        nodes = [node for node in graph.get("nodes", []) if node.get("type") == "Constraint" and node.get("name") == constraint]
        edges = [edge for edge in graph.get("edges", []) if edge.get("to") == f"constraint::{constraint}"]
        return {
            "evidence_ref": record.evidence_ref,
            "constraint": constraint,
            "nodes": nodes,
            "edges": edges,
        }

    def scenario_replay(self, record: EvidenceRecord, scenario_id: int) -> Optional[Dict[str, object]]:
        scenarios = record.snapshot.get("scenarios", {}).get("scenarios") if isinstance(record.snapshot.get("scenarios"), dict) else None
        if not isinstance(scenarios, list):
            return None
        for scenario in scenarios:
            if int(scenario.get("id")) == scenario_id:
                return scenario
        return None
