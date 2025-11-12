from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.agent.schemas import PlanPack, Step
from packages.agent.executor import PlanExecutor, STORE
from packages.archetypes import build_ops_from_template
from packages.kernel_common.logging import configure_logging

app = FastAPI(
    title="Dyocense Planner Service",
    version="0.1.0",
    description="Structured plan creation and execution for forecasting and optimisation.",
)

logger = configure_logging("plan-service")


class PlanCreateRequest(BaseModel):
    goal: str
    tenant_id: Optional[str] = None
    project_id: Optional[str] = None
    template_id: str = Field(default="forecasting_basic", description="Archetype/Template ID")
    horizon: int = Field(default=3, ge=1, le=12)
    series: Optional[List[Dict[str, Any]]] = None


class PlanCreateResponse(BaseModel):
    plan_id: str
    status: str
    plan: PlanPack


@app.post("/v1/plan", response_model=PlanCreateResponse)
def create_plan(body: PlanCreateRequest) -> PlanCreateResponse:
    plan_id = body.project_id or f"plan-{uuid.uuid4().hex[:12]}"
    logger.info(
        "Creating plan %s for goal=%s tenant=%s template=%s",
        plan_id,
        body.goal,
        body.tenant_id or "tenant-demo",
        body.template_id,
    )

    # Build baseline OPS from template for optimisation and policy steps
    ops = build_ops_from_template(
        body.template_id,
        body.goal,
        body.tenant_id or "tenant-demo",
        plan_id,
        {},
    )

    steps: List[Step] = []

    # Forecast step
    steps.append(
        Step(
            step_id="forecast_1",
            type="forecast",
            tool="forecast_service",
            inputs={"horizon": body.horizon, "series": body.series or []},
            rationale="Generate demand forecast for planning horizon.",
        )
    )

    # Policy evaluation
    steps.append(
        Step(
            step_id="policy_1",
            type="policy_eval",
            tool="policy_service",
            depends_on=["forecast_1"],
            inputs={"ops": ops, "tenant_id": body.tenant_id or "tenant-demo"},
            rationale="Evaluate policy constraints for the plan.",
        )
    )

    # Optimisation depends on forecast
    steps.append(
        Step(
            step_id="optimise_1",
            type="optimise",
            tool="optimiser_service",
            depends_on=["forecast_1"],
            inputs={"ops": ops},
            rationale="Compute optimal actions using OPS and forecast.",
        )
    )

    # Diagnostics
    steps.append(
        Step(
            step_id="diagnostics_1",
            type="diagnostics",
            tool="diagnostician_service",
            depends_on=["optimise_1"],
            inputs={"ops": ops, "tenant_id": body.tenant_id or "tenant-demo", "solution": {"ref": "optimise_1"}},
            rationale="Identify potential issues or constraints.",
        )
    )

    # Explain
    steps.append(
        Step(
            step_id="explain_1",
            type="explain",
            tool="explainer_service",
            depends_on=["optimise_1", "forecast_1"],
            inputs={"goal": body.goal, "solution": {"ref": "optimise_1"}, "forecasts": {"ref": "forecast_1"}},
            rationale="Generate human-friendly explanation of the plan.",
        )
    )

    # Persist (evidence)
    steps.append(
        Step(
            step_id="persist_1",
            type="persist",
            tool="evidence_service",
            depends_on=["optimise_1", "explain_1"],
            inputs={
                "payload": {
                    "run_id": plan_id,
                    "tenant_id": body.tenant_id or "tenant-demo",
                    "ops": ops,
                    # The executor will write step outputs to artifacts and persist evidence
                }
            },
            rationale="Store artifacts and evidence record.",
        )
    )

    plan = PlanPack(
        id=plan_id,
        goal=body.goal,
        context={"tenant_id": body.tenant_id, "template_id": body.template_id, "horizon": body.horizon},
        steps=steps,
        status="draft",
    )
    STORE.put(plan)
    return PlanCreateResponse(plan_id=plan_id, status=plan.status, plan=plan)


class PlanExecuteResponse(BaseModel):
    plan_id: str
    status: str


@app.post("/v1/plan/execute/{plan_id}", response_model=PlanExecuteResponse)
def execute_plan(plan_id: str, background_tasks: BackgroundTasks) -> PlanExecuteResponse:
    logger.info("Executing plan %s", plan_id)
    plan = STORE.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    def _resolve_refs() -> None:
        """Resolve {"ref": step_id} in inputs to artifact JSON for simple chaining."""
        # Very simple resolver: look up previous step output files in artifacts dir
        from pathlib import Path
        import json

        plan_dir = (Path("artifacts/plans") / plan_id)
        outputs: dict[str, dict] = {}
        # map common artifact names if present
        for name in ["forecast", "policy", "solution", "diagnostics", "explanation", "evidence"]:
            p = plan_dir / f"{name}.json"
            if p.exists():
                try:
                    outputs[name] = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    pass

        # Replace known refs by artifact content when possible
        for s in plan.steps:
            def _replace(obj):
                if isinstance(obj, dict) and set(obj.keys()) == {"ref"}:
                    ref = obj["ref"]
                    # heuristic mapping from step_id to artifact name
                    mapping = {
                        "forecast_1": outputs.get("forecast"),
                        "policy_1": outputs.get("policy"),
                        "optimise_1": outputs.get("solution"),
                        "diagnostics_1": outputs.get("diagnostics"),
                        "explain_1": outputs.get("explanation"),
                    }
                    return mapping.get(ref, obj)
                if isinstance(obj, list):
                    return [_replace(x) for x in obj]
                if isinstance(obj, dict):
                    return {k: _replace(v) for k, v in obj.items()}
                return obj
            s.inputs = _replace(s.inputs)  # type: ignore

    def _run():
        _resolve_refs()
        executor = PlanExecutor()
        executor.execute(plan)

    background_tasks.add_task(_run)
    plan.status = "executing"
    STORE.put(plan)
    return PlanExecuteResponse(plan_id=plan_id, status=plan.status)


@app.get("/v1/plan/{plan_id}", response_model=PlanPack)
def get_plan(plan_id: str) -> PlanPack:
    logger.debug("Fetching plan %s", plan_id)
    plan = STORE.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@app.delete("/v1/plan/{plan_id}")
def cancel_plan(plan_id: str) -> Dict[str, str]:
    plan = STORE.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status in ("completed", "failed", "cancelled"):
        return {"plan_id": plan_id, "status": plan.status}
    plan.status = "cancelled"
    # executor will skip remaining steps if it checks status; for MVP we just mark it
    STORE.put(plan)
    return {"plan_id": plan_id, "status": plan.status}
