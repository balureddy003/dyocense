from __future__ import annotations

import copy
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging
from packages.kernel_common.telemetry import set_span_attributes, start_span
from packages.versioning import GLOBAL_LEDGER, GoalVersion
from services.compiler.main import build_ops_document

logger = configure_logging("scenario-service")

app = FastAPI(
    title="Dyocense Scenario Service",
    version="0.2.0",
    description="Manages goal/plan scenarios and what-if deltas on top of the version ledger.",
)


class ScenarioRequest(BaseModel):
    base_version_id: str = Field(..., description="Baseline version identifier.")
    label: str | None = Field(default=None, description="Friendly name for the scenario.")
    goal_override: str | None = Field(default=None, description="Optional new goal text.")
    data_overrides: Dict[str, Any] | None = Field(
        default=None, description="Overrides for structured inputs used during compile."
    )
    parameter_overrides: Dict[str, Dict[str, Any]] | None = Field(
        default=None, description="Direct overrides for OPS parameters after compilation."
    )
    recompute: bool = Field(
        default=True,
        description="When true, re-run the compiler pipeline; otherwise clone baseline ops before applying overrides.",
    )
    use_llm: bool = Field(default=True, description="Enable LLM when recomputing.")


class ScenarioResponse(BaseModel):
    version_id: str
    base_version_id: str
    label: str | None
    diff: List[Dict[str, Any]]
    ops: Dict


@app.post("/v1/scenarios", response_model=ScenarioResponse)
def create_scenario(
    request: ScenarioRequest,
    identity: dict = Depends(require_auth),
) -> ScenarioResponse:
    base_version = GLOBAL_LEDGER.get(request.base_version_id)
    if not base_version:
        raise HTTPException(status_code=404, detail="Base version not found")
    if base_version.tenant_id != identity["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied for base version")

    span_attributes = {
        "scenario.base_version_id": request.base_version_id,
        "scenario.recompute": request.recompute,
        "scenario.use_llm": request.use_llm,
    }
    with start_span("scenario.create", span_attributes) as span:
        goal = request.goal_override or base_version.goal
        data_inputs = _merge_data_inputs(base_version.data_inputs or {}, request.data_overrides or {})

        if request.recompute:
            ops, goal_pack = build_ops_document(
                goal,
                base_version.tenant_id,
                base_version.project_id,
                data_inputs=data_inputs,
                use_llm=request.use_llm,
            )
            version_id = goal_pack["version_id"]
            GLOBAL_LEDGER.annotate(
                version_id,
                parent_version_id=base_version.version_id,
                label=request.label or f"Scenario of {base_version.version_id}",
                data_inputs=data_inputs,
            )
            scenario_version = GLOBAL_LEDGER.get(version_id)
            set_span_attributes(span, {"scenario.source": "compiler"})
        else:
            ops = copy.deepcopy(base_version.ops)
            if request.parameter_overrides:
                for key, override in request.parameter_overrides.items():
                    parameters = ops.setdefault("parameters", {})
                    current = parameters.get(key, {})
                    if isinstance(current, dict):
                        current.update(override)
                    else:
                        parameters[key] = override
            version_id = _mint_version_id()
            ops.setdefault("metadata", {})["version_id"] = version_id
            scenario_version = GoalVersion(
                version_id=version_id,
                tenant_id=base_version.tenant_id,
                project_id=base_version.project_id,
                goal=goal,
                ops=copy.deepcopy(ops),
                data_inputs=data_inputs,
                playbook_id=base_version.playbook_id,
                knowledge_snippets=base_version.knowledge_snippets,
                parent_version_id=base_version.version_id,
                label=request.label or f"Scenario of {base_version.version_id}",
                created_at=datetime.now(timezone.utc),
                goal_hash=hashlib.sha256((goal or "").encode("utf-8")).hexdigest(),
                retrieval=base_version.retrieval,
                provenance={
                    "compiler_source": "clone",
                    "model": base_version.provenance.get("model"),
                    "duration_seconds": 0.0,
                },
            )
            GLOBAL_LEDGER.record(scenario_version)
            set_span_attributes(span, {"scenario.source": "clone"})

        if request.parameter_overrides and request.recompute:
            for key, override in request.parameter_overrides.items():
                parameters = ops.setdefault("parameters", {})
                current = parameters.get(key, {})
                if isinstance(current, dict):
                    current.update(override)
                else:
                    parameters[key] = override
            GLOBAL_LEDGER.annotate(
                scenario_version.version_id,
                ops=ops,
            )

        diff = _diff_parameters(base_version.ops, ops)
        set_span_attributes(
            span,
            {
                "scenario.version_id": version_id,
                "scenario.diff.size": len(diff),
            },
        )
        logger.info(
            "Created scenario %s from %s (tenant=%s)",
            version_id,
            base_version.version_id,
            base_version.tenant_id,
        )
        return ScenarioResponse(
            version_id=version_id,
            base_version_id=base_version.version_id,
            label=scenario_version.label,
            diff=diff,
            ops=ops,
        )


@app.get("/v1/scenarios/{version_id}", response_model=GoalVersion)
def get_scenario(version_id: str, identity: dict = Depends(require_auth)) -> GoalVersion:
    version = GLOBAL_LEDGER.get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    if version.tenant_id != identity["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied for version")
    return version


@app.get("/v1/scenarios", response_model=List[GoalVersion])
def list_scenarios(
    project_id: str,
    identity: dict = Depends(require_auth),
) -> List[GoalVersion]:
    versions = GLOBAL_LEDGER.list_for_project(identity["tenant_id"], project_id)
    return [version for version in versions if version.parent_version_id]


def _merge_data_inputs(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)  # type: ignore[index]
        else:
            merged[key] = value
    return merged


def _diff_parameters(base_ops: Dict[str, Any], new_ops: Dict[str, Any]) -> List[Dict[str, Any]]:
    base_params = base_ops.get("parameters", {}) or {}
    new_params = new_ops.get("parameters", {}) or {}
    diff: List[Dict[str, Any]] = []
    for key, base_value in base_params.items():
        new_value = new_params.get(key)
        if new_value != base_value:
            diff.append({"path": f"parameters.{key}", "before": base_value, "after": new_value})
    for key, new_value in new_params.items():
        if key not in base_params:
            diff.append({"path": f"parameters.{key}", "before": None, "after": new_value})
    return diff


def _mint_version_id() -> str:
    return f"ver-{uuid.uuid4().hex[:12]}"
