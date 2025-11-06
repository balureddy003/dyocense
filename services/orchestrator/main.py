from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging
from packages.archetypes import build_ops_from_template
from services.diagnostician.main import diagnose_ops
from services.evidence.main import persist_evidence_record
from services.explainer.main import generate_explanation
from services.forecast.main import ForecastRequest, ForecastSeries, compute_forecast
from services.optimiser.main import optimise_ops_document
from services.policy.main import evaluate_ops_policy

try:  # optional dependency in case accounts service not initialised
    from packages.accounts.repository import (
        get_tenant,
        get_plan,
        record_playbook_usage,
        SubscriptionLimitError,
    )
except Exception:  # pragma: no cover - optional
    get_tenant = None
    get_plan = None
    record_playbook_usage = None

    class SubscriptionLimitError(Exception):
        pass

logger = configure_logging("orchestrator-service")

ARTIFACT_ROOT = Path("artifacts/runs")
ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Dyocense Orchestrator Service",
    version="0.6.0",
    description="Unified goal→decision pipeline with background execution.",
)


@dataclass
class RunState:
    status: str
    goal: str
    tenant_id: str
    project_id: str
    template_id: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


RUNS: Dict[str, RunState] = {}


class RunRequest(BaseModel):
    goal: str = Field(..., description="Natural-language goal.")
    project_id: str | None = Field(default=None, description="Project identifier.")
    horizon: int = Field(2, ge=1, le=12)
    # Make optional to accept legacy payloads with only archetype_id
    template_id: Optional[str] = Field(
        default=None, description="Template identifier from the catalog."
    )
    # Backward compatibility
    archetype_id: Optional[str] = Field(None, description="Legacy field - use template_id instead.")
    data_inputs: Dict[str, List[Dict[str, Any]]] | None = Field(
        default=None, description="Structured data payloads (CSV parsed rows)."
    )
    series: List[ForecastSeries] | None = Field(
        default=None,
        description="Optional time-series data; if omitted, demand parameters drive forecasts.",
    )


class RunResponse(BaseModel):
    run_id: str
    status: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    goal: str
    template_id: Optional[str] = None
    archetype_id: Optional[str] = None  # Backward compatibility
    result: Optional[dict]
    error: Optional[str]


class RunListResponse(BaseModel):
    runs: List[RunStatusResponse]


@app.post("/v1/runs", response_model=RunResponse, status_code=202)
def submit_run(
    body: RunRequest,
    background_tasks: BackgroundTasks,
    identity: dict = Depends(require_auth),
) -> RunResponse:
    # Backward compatibility: use archetype_id if template_id not provided
    template_id = body.template_id or body.archetype_id
    if not template_id:
        raise HTTPException(status_code=400, detail="template_id is required")
    
    # Only enforce tenant limits if we have a real database connection
    if get_tenant and get_plan:
        tenant = get_tenant(identity["tenant_id"])
        if tenant is not None:  # Only check limits if tenant exists
            plan = get_plan(tenant.plan_tier)
            if tenant.usage.playbooks >= plan.limits.max_playbooks:
                raise HTTPException(
                    status_code=403,
                    detail="Playbook storage limit reached for your subscription tier.",
                )

    run_id = body.project_id or f"run-{uuid.uuid4().hex[:12]}"
    state = RunState(
        status="pending",
        goal=body.goal,
        tenant_id=identity["tenant_id"],
        project_id=run_id,
        template_id=template_id,
    )
    RUNS[run_id] = state
    background_tasks.add_task(_execute_run, run_id, body, identity["tenant_id"], template_id)
    logger.info("Enqueued run %s for tenant %s", run_id, identity["tenant_id"])
    return RunResponse(run_id=run_id, status="pending")


@app.get("/v1/runs/{run_id}", response_model=RunStatusResponse)
def get_run_status(run_id: str) -> RunStatusResponse:
    state = RUNS.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunStatusResponse(
        run_id=run_id,
        status=state.status,
        goal=state.goal,
        template_id=state.template_id,
        archetype_id=state.template_id,  # Backward compatibility
        result=state.result,
        error=state.error,
    )


@app.get("/v1/runs", response_model=RunListResponse)
def list_runs() -> RunListResponse:
    return RunListResponse(
        runs=[
            RunStatusResponse(
                run_id=run_id,
                status=state.status,
                goal=state.goal,
                template_id=state.template_id,
                archetype_id=state.template_id,  # Backward compatibility
                result=state.result,
                error=state.error,
            )
            for run_id, state in sorted(RUNS.items(), key=lambda item: item[0], reverse=True)
        ]
    )


def _execute_run(run_id: str, request: RunRequest, tenant_id: str, template_id: str) -> None:
    state = RUNS[run_id]
    state.status = "running"
    try:
        ops = build_ops_from_template(
            template_id,
            request.goal,
            tenant_id,
            run_id,
            request.data_inputs or {},
        )
        series = request.series
        if series is None:
            demand = ops.get("parameters", {}).get("demand", {})
            series = [
                ForecastSeries(name=name, values=[float(value)]) for name, value in demand.items()
            ]
        forecast_resp = compute_forecast(series, request.horizon)
        policy_resp = evaluate_ops_policy(ops, tenant_id)
        solution = optimise_ops_document(ops)
        diagnostics = diagnose_ops(ops, solution, tenant_id)
        explanation = generate_explanation(
            request.goal,
            solution,
            forecast_resp.forecasts,
            policy_resp.model_dump(),
            diagnostics.model_dump(),
        )
        artifacts = _persist_artifacts(run_id, solution, explanation, diagnostics)
        evidence = persist_evidence_record(
            {
                "run_id": run_id,
                "tenant_id": tenant_id,
                "ops": ops,
                "solution": solution,
                "explanation": explanation.model_dump(),
                "artifacts": artifacts,
            }
        )

        state.result = {
            "ops": ops,
            "forecast": forecast_resp.model_dump(),
            "policy": policy_resp.model_dump(),
            "solution": solution,
            "diagnostics": diagnostics.model_dump(),
            "explanation": explanation.model_dump(),
            "artifacts": artifacts,
            "evidence": evidence.model_dump(),
        }
        if record_playbook_usage:
            try:
                record_playbook_usage(tenant_id, increment=1)
            except (SubscriptionLimitError, ValueError) as exc:
                # ValueError raised when tenant not found - safe to ignore in dev/demo mode
                logger.warning("Unable to record playbook usage for tenant %s: %s", tenant_id, exc)
        state.status = "completed"
        logger.info("Run %s completed", run_id)
    except Exception as exc:  # pragma: no cover - ensures failure surfaced
        logger.exception("Run %s failed: %s", run_id, exc)
        state.status = "failed"
        state.error = str(exc)


def _persist_artifacts(run_id: str, solution: dict, explanation, diagnostics) -> Dict[str, dict]:
    run_dir = ARTIFACT_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    artifacts: Dict[str, dict] = {}

    solution_path = run_dir / "solution.json"
    solution_path.write_text(json.dumps(solution, indent=2), encoding="utf-8")
    artifacts["solution_pack"] = {"type": "json", "path": str(solution_path)}

    explanation_payload = explanation.model_dump() if hasattr(explanation, "model_dump") else explanation
    explanation_path = run_dir / "explanation.json"
    explanation_path.write_text(json.dumps(explanation_payload, indent=2), encoding="utf-8")
    artifacts["explanation"] = {"type": "json", "path": str(explanation_path)}

    diagnostics_payload = diagnostics.model_dump() if hasattr(diagnostics, "model_dump") else diagnostics
    diagnostics_path = run_dir / "diagnostics.json"
    diagnostics_path.write_text(json.dumps(diagnostics_payload, indent=2), encoding="utf-8")
    artifacts["diagnostics"] = {"type": "json", "path": str(diagnostics_path)}

    return artifacts
