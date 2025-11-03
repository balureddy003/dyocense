from __future__ import annotations

import copy
import hashlib
import os
from datetime import datetime, timezone
import uuid
from typing import Any, Dict

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from packages.kernel_common import load_schema
from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging
from packages.kernel_common.telemetry import set_span_attributes, start_span
from packages.compiler_pipeline import CompileOrchestrator, CompileRequestContext, CompileTelemetry
from packages.knowledge import KnowledgeClient
from packages.playbooks import PlaybookRegistry, load_default_playbooks
from packages.versioning import GLOBAL_LEDGER, GoalVersion

logger = configure_logging("compiler-service")
knowledge_client = KnowledgeClient()
playbook_registry = PlaybookRegistry(load_default_playbooks())
telemetry = CompileTelemetry()
orchestrator = CompileOrchestrator(knowledge_client, playbook_registry, telemetry)


def build_ops_document(
    goal: str,
    tenant_id: str,
    project_id: str,
    data_inputs: Dict[str, Any] | None = None,
    use_llm: bool = True,
) -> tuple[dict, dict]:
    with start_span(
        "compiler.build_ops",
        {
            "goal.length": len(goal or ""),
            "tenant_id": tenant_id,
            "project_id": project_id,
            "use_llm": use_llm,
        },
    ) as span:
        base_ops = _base_metadata(goal, tenant_id, project_id)
        context = CompileRequestContext(
            goal=goal,
            tenant_id=tenant_id,
            project_id=project_id,
            data_inputs=data_inputs,
            use_llm=use_llm,
        )
        artifacts = orchestrator.generate_ops(context, base_ops)
        logger.debug(
            "Compiling goal '%s' for tenant=%s project=%s (use_llm=%s)",
            goal,
            tenant_id,
            project_id,
            use_llm,
        )
        ops_document: dict
        if artifacts.llm_ops:
            merged = _merge_ops(base_ops, artifacts.llm_ops)
            if _has_required_sections(merged):
                logger.info(
                    "Generated OPS via LLM for goal '%s' (playbook=%s snippets=%s)",
                    goal,
                    getattr(artifacts.playbook, "id", None),
                    len(artifacts.snippets),
                )
                ops_document = merged
                set_span_attributes(
                    span,
                    {
                        "compiler.playbook_id": getattr(artifacts.playbook, "id", None),
                        "compiler.snippet_count": len(artifacts.snippets),
                        "compiler.source": "llm",
                    },
                )
            else:
                logger.warning("LLM OPS missing sections; using stub fallback")
                ops_document = _stub_ops(goal, tenant_id, project_id, data_inputs, artifacts)
                set_span_attributes(span, {"compiler.source": "fallback_incomplete"})
        else:
            logger.warning("LLM compiler unavailable or failed; returning stub OPS")
            ops_document = _stub_ops(goal, tenant_id, project_id, data_inputs, artifacts)
            set_span_attributes(span, {"compiler.source": "fallback"})

        goal_version = _record_version(
            ops_document,
            goal,
            tenant_id,
            project_id,
            data_inputs,
            artifacts,
        )
        version_id = goal_version.version_id
        ops_document.setdefault("metadata", {})["version_id"] = version_id
        set_span_attributes(span, {"compiler.version_id": version_id})
        goal_pack = _build_goal_pack(goal_version)
        set_span_attributes(span, {"compiler.goal_hash": goal_version.goal_hash})
        return ops_document, goal_pack


app = FastAPI(
    title="Dyocense Compiler Service",
    version="0.7.0",
    description="Phase 2 compiler with knowledge retrieval, playbooks, and LLM orchestration.",
)


class CompileRequest(BaseModel):
    goal: str = Field(..., description="Natural-language objective from the user.")
    tenant_id: str | None = Field("demo-tenant", description="Tenant identifier.")
    project_id: str = Field("phase1-demo", description="Project identifier.")
    data_inputs: Dict[str, Any] | None = Field(
        default=None,
        description="Optional structured inputs (e.g., demand, costs).",
    )


class CompileResponse(BaseModel):
    ops: dict = Field(..., description="Optimization Problem Spec JSON document.")
    goal_pack: dict = Field(..., description="Immutable GoalPack record emitted for this compile.")
    version_id: str = Field(..., description="Version identifier recorded in ledger.")
    schema: dict = Field(
        default_factory=lambda: load_schema("ops.schema.json"),
        description="Inline OPS schema snapshot.",
    )
    goalpack_schema: dict = Field(
        default_factory=lambda: load_schema("goalpack.schema.json"),
        description="GoalPack contract snapshot for clients.",
    )


@app.post("/v1/compile", response_model=CompileResponse)
def compile_goal(body: CompileRequest, identity: dict = Depends(require_auth)) -> CompileResponse:
    """Produce an OPS document using the Phase 2 compiler pipeline."""
    tenant_id = body.tenant_id or identity["tenant_id"]
    ops_document, goal_pack = build_ops_document(
        body.goal,
        tenant_id,
        body.project_id,
        data_inputs=body.data_inputs,
        use_llm=True,
    )
    logger.info(
        "Generated OPS for goal '%s' (tenant=%s)",
        body.goal,
        tenant_id,
    )
    version_id = goal_pack["version_id"]
    return CompileResponse(ops=ops_document, goal_pack=goal_pack, version_id=version_id)


def _base_metadata(goal: str, tenant_id: str, project_id: str) -> dict:
    logger.debug("Falling back to stub compiler for goal '%s'", goal)
    return {
        "metadata": {
            "ops_version": "1.0.0",
            "problem_type": "inventory_planning",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_tags": ["goal", goal[:32]],
        }
    }


def _merge_ops(base_ops: dict, llm_ops: dict) -> dict:
    merged = dict(llm_ops)
    metadata = merged.get("metadata", {})
    metadata.update(base_ops.get("metadata", {}))
    merged["metadata"] = metadata
    return merged


def _has_required_sections(ops: dict) -> bool:
    required = [
        "objective",
        "decision_variables",
        "parameters",
        "constraints",
        "kpis",
    ]
    return all(key in ops for key in required)


def _stub_ops(
    goal: str,
    tenant_id: str,
    project_id: str,
    data_inputs: Dict[str, Any] | None = None,
    artifacts=None,
) -> dict:
    demand = _extract_table(data_inputs, "demand", "quantity")
    holding = _extract_table(data_inputs, "holding_cost", "cost")

    if not demand:
        demand = {"widget": 120, "gadget": 95}
    if not holding:
        holding = {"widget": 2.5, "gadget": 1.75}

    metadata = {
        "metadata": {
            "ops_version": "1.0.0",
            "problem_type": "inventory_planning",
            "tenant_id": tenant_id,
            "project_id": project_id,
            "run_tags": ["stub", goal[:32]],
        },
    }
    if artifacts:
        if getattr(artifacts, "snippets", None):
            metadata["metadata"]["knowledge_snippets"] = [
                snippet.get("document_id") if isinstance(snippet, dict) else snippet.document_id  # type: ignore[attr-defined]
                for snippet in artifacts.snippets
            ]
        if getattr(artifacts, "playbook", None):
            playbook = artifacts.playbook
            metadata["metadata"]["playbook_id"] = getattr(playbook, "id", None)
            metadata["metadata"]["playbook_version"] = getattr(playbook, "version", None)

    return {
        **metadata,
        "objective": {
            "sense": "min",
            "expression": "sum_{sku} holding_cost[sku] * stock[sku]",
        },
        "decision_variables": [
            {
                "name": "stock",
                "type": "integer",
                "lb": 0,
                "ub": 1000,
                "index_sets": ["sku"],
            }
        ],
        "parameters": {
            "holding_cost": holding,
            "demand": demand,
        },
        "constraints": [
            {
                "name": "demand_satisfaction",
                "for_all": "sku",
                "expression": "stock[sku] >= demand[sku]",
            }
        ],
        "kpis": [
            {
                "name": "total_holding_cost",
                "expression": "sum_{sku} holding_cost[sku] * stock[sku]",
            }
        ],
        "validation_notes": ["Generated via fallback compiler stub."],
    }


def _extract_table(data_inputs: Dict[str, Any] | None, key: str, value_field: str) -> Dict[str, float]:
    if not data_inputs:
        return {}
    rows = data_inputs.get(key)
    if not isinstance(rows, list):
        return {}
    result: Dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        sku = row.get("sku") or row.get("id")
        value = row.get(value_field)
        if sku is None or value is None:
            continue
        try:
            result[str(sku)] = float(value)
        except (TypeError, ValueError):
            logger.debug("Skipping row with invalid value: %s", row)
            continue
    return result


def _record_version(
    ops: dict,
    goal: str,
    tenant_id: str,
    project_id: str,
    data_inputs: Dict[str, Any] | None,
    artifacts,
) -> GoalVersion:
    version_id = ops.get("metadata", {}).get("version_id") or f"ver-{uuid.uuid4().hex[:12]}"
    knowledge_snippets = ops.get("metadata", {}).get("knowledge_snippets", [])
    playbook_id = ops.get("metadata", {}).get("playbook_id")
    created_at = datetime.now(timezone.utc)
    goal_hash = hashlib.sha256((goal or "").encode("utf-8")).hexdigest()
    dataset_version = os.getenv("ICEBERG_SNAPSHOT") or os.getenv("DATASET_VERSION")
    retrieval = {
        "snippet_ids": list(knowledge_snippets),
        "snippet_count": len(knowledge_snippets),
    }
    if dataset_version:
        retrieval["dataset_version"] = dataset_version
    provenance = {
        "compiler_source": artifacts.source,
        "model": artifacts.model_name,
        "duration_seconds": artifacts.duration_seconds,
    }
    version = GoalVersion(
        version_id=version_id,
        tenant_id=tenant_id,
        project_id=project_id,
        goal=goal,
        ops=copy.deepcopy(ops),
        data_inputs=copy.deepcopy(data_inputs) if data_inputs else None,
        playbook_id=playbook_id,
        knowledge_snippets=list(knowledge_snippets),
        parent_version_id=None,
        label=None,
        created_at=created_at,
        goal_hash=goal_hash,
        retrieval=retrieval,
        provenance=provenance,
    )
    GLOBAL_LEDGER.record(version)
    return version


def _build_goal_pack(version: GoalVersion) -> dict:
    created_at = version.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    goal_pack = {
        "version_id": version.version_id,
        "goal": version.goal,
        "tenant_id": version.tenant_id,
        "project_id": version.project_id,
        "created_at": created_at.isoformat(),
        "goal_hash": version.goal_hash,
        "ops": copy.deepcopy(version.ops),
        "data_inputs": copy.deepcopy(version.data_inputs) if version.data_inputs else None,
        "retrieval": version.retrieval,
        "provenance": version.provenance,
    }
    if version.playbook_id:
        goal_pack["playbook"] = {
            "id": version.playbook_id,
            "version": version.ops.get("metadata", {}).get("playbook_version"),
        }
    if version.parent_version_id:
        goal_pack["scenario"] = {
            "parent_version_id": version.parent_version_id,
            "label": version.label,
        }
    return goal_pack
