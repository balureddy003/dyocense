from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone

from pydantic import BaseModel

from packages.agent.schemas import PlanPack, Step
from packages.archetypes import build_ops_from_template
from services.forecast.main import ForecastSeries, compute_forecast
from services.policy.main import evaluate_ops_policy
from services.optimiser.main import optimise_ops_document
from services.diagnostician.main import diagnose_ops
from services.explainer.main import generate_explanation
from services.evidence.main import persist_evidence_record
from packages.agent.tracing import trace_event


ARTIFACT_ROOT = Path("artifacts/plans")
ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)


class PlanStore:
    """Very small in-memory + disk-backed store for PlanPacks."""

    def __init__(self) -> None:
        self._plans: Dict[str, PlanPack] = {}

    def put(self, plan: PlanPack) -> None:
        self._plans[plan.id] = plan
        self._persist(plan)

    def get(self, plan_id: str) -> PlanPack | None:
        return self._plans.get(plan_id)

    def _persist(self, plan: PlanPack) -> None:
        plan_dir = ARTIFACT_ROOT / plan.id
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")


STORE = PlanStore()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save_artifact(plan_id: str, name: str, payload: Dict[str, Any]) -> str:
    plan_dir = ARTIFACT_ROOT / plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)
    path = plan_dir / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


class PlanExecutor:
    def __init__(self) -> None:
        # Timeouts configurable via env (seconds)
        self.forecast_timeout = int(os.getenv("PLAN_FORECAST_TIMEOUT_SEC", "15"))
        self.optimise_timeout = int(os.getenv("PLAN_OPTIMISE_TIMEOUT_SEC", "30"))
        self.enable_tracing = os.getenv("PLAN_ENABLE_TRACING", "1").lower() in ("1", "true", "yes")

    def _artifact_path(self, plan_id: str, name: str) -> Path:
        return ARTIFACT_ROOT / plan_id / f"{name}.json"

    def _load_artifact_json(self, plan_id: str, name: str) -> Dict[str, Any] | None:
        p = self._artifact_path(plan_id, name)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def _resolve_refs(self, plan_id: str, obj: Any) -> Any:
        """Resolve {"ref": step_id} to artifact JSON using heuristic mapping."""
        mapping = {
            "forecast_1": "forecast",
            "policy_1": "policy",
            "optimise_1": "solution",
            "diagnostics_1": "diagnostics",
            "explain_1": "explanation",
        }
        def _replace(x: Any) -> Any:
            if isinstance(x, dict) and set(x.keys()) == {"ref"}:
                step_id = x["ref"]
                name = mapping.get(step_id)
                if name:
                    payload = self._load_artifact_json(plan_id, name)
                    return payload if payload is not None else x
                return x
            if isinstance(x, list):
                return [_replace(i) for i in x]
            if isinstance(x, dict):
                return {k: _replace(v) for k, v in x.items()}
            return x
        return _replace(obj)

    def execute(self, plan: PlanPack) -> PlanPack:
        plan.status = "executing"
        STORE.put(plan)

        deps = plan.build_dependency_index()
        step_index = {s.step_id: s for s in plan.steps}
        context_outputs: Dict[str, Any] = {}
        name_by_step = {
            "forecast_1": "forecast",
            "policy_1": "policy",
            "optimise_1": "solution",
            "diagnostics_1": "diagnostics",
            "explain_1": "explanation",
            "persist_1": "evidence",
        }

        def resolve_inputs(raw_inputs: Dict[str, Any]) -> Dict[str, Any]:
            # First resolve refs from in-memory context, then fall back to artifact files
            def _replace(x: Any) -> Any:
                if isinstance(x, dict) and set(x.keys()) == {"ref"}:
                    step_id = x["ref"]
                    name = name_by_step.get(step_id)
                    if name and name in context_outputs:
                        return context_outputs[name]
                    # fall back to disk if context missing
                    payload = self._load_artifact_json(plan.id, name) if name else None
                    return payload if payload is not None else x
                if isinstance(x, list):
                    return [_replace(i) for i in x]
                if isinstance(x, dict):
                    return {k: _replace(v) for k, v in x.items()}
                return x
            return _replace(raw_inputs)

        for step in plan.steps:
            if any(step_index[d].status != "succeeded" for d in deps.get(step.step_id, [])):
                step.status = "skipped"
                continue

            step.actual_start = _ts()
            step.status = "running"
            STORE.put(plan)
            trace_event(plan.id, "step.start", {"step_id": step.step_id, "type": step.type})

            try:
                if self.enable_tracing:
                    step.trace_id = step.trace_id or plan.trace_root_id or plan.id
                    step.span_id = f"{step.step_id}-{int(time.time()*1000)}"
                inputs = resolve_inputs(step.inputs)
                if step.type == "forecast":
                    start_time = time.time()
                    series = inputs.get("series") or []
                    horizon = int(inputs.get("horizon", 3))
                    series_obj = [ForecastSeries(**e) if isinstance(e, dict) else e for e in series]
                    forecast = compute_forecast(series_obj, horizon)
                    elapsed = time.time() - start_time
                    ref = _save_artifact(plan.id, "forecast", forecast.model_dump())
                    context_outputs["forecast"] = forecast.model_dump()
                    step.output_ref = ref
                    step.metrics.update({
                        "model_used": forecast.model_dump().get("model_used", "unknown"),
                        "elapsed_sec": round(elapsed, 3)
                    })
                    if elapsed > self.forecast_timeout:
                        plan.risks.append(f"Forecast exceeded timeout {self.forecast_timeout}s (elapsed {elapsed:.2f}s)")
                elif step.type == "policy_eval":
                    ops = inputs["ops"]
                    tenant_id = inputs.get("tenant_id")
                    policy = evaluate_ops_policy(ops, tenant_id)
                    ref = _save_artifact(plan.id, "policy", policy.model_dump())
                    context_outputs["policy"] = policy.model_dump()
                    step.output_ref = ref
                elif step.type == "optimise":
                    start_time = time.time()
                    ops = inputs["ops"]
                    try:
                        solution = optimise_ops_document(ops)
                    except Exception as exc:
                        solution = {
                            "objective_value": None,
                            "solver_name": "stub-fallback",
                            "status": "fallback",
                            "error": str(exc)
                        }
                        plan.risks.append("Optimiser failed; stub fallback used.")
                    elapsed = time.time() - start_time
                    ref = _save_artifact(plan.id, "solution", solution)
                    context_outputs["solution"] = solution
                    step.output_ref = ref
                    step.metrics.update({"objective_value": solution.get("objective_value"), "elapsed_sec": round(elapsed, 3)})
                    if elapsed > self.optimise_timeout:
                        plan.risks.append(f"Optimisation exceeded timeout {self.optimise_timeout}s (elapsed {elapsed:.2f}s)")
                elif step.type == "diagnostics":
                    ops = inputs["ops"]
                    tenant_id = inputs.get("tenant_id")
                    solution = inputs.get("solution")
                    diag = diagnose_ops(ops, solution, tenant_id)
                    ref = _save_artifact(plan.id, "diagnostics", diag.model_dump())
                    context_outputs["diagnostics"] = diag.model_dump()
                    step.output_ref = ref
                elif step.type == "explain":
                    goal = inputs.get("goal")
                    solution = inputs.get("solution") or context_outputs.get("solution")
                    forecasts = inputs.get("forecasts") or context_outputs.get("forecast") or []
                    policy = inputs.get("policy") or context_outputs.get("policy")
                    diagnostics = inputs.get("diagnostics") or context_outputs.get("diagnostics")
                    if solution is None:
                        raise ValueError("Explanation step missing solution reference")
                    explanation = generate_explanation(goal, solution, forecasts, policy, diagnostics)
                    ref = _save_artifact(plan.id, "explanation", explanation.model_dump())
                    context_outputs["explanation"] = explanation.model_dump()
                    step.output_ref = ref
                elif step.type == "persist":
                    payload = inputs["payload"]
                    ev = persist_evidence_record(payload)
                    ref = _save_artifact(plan.id, "evidence", ev.model_dump())
                    context_outputs["evidence"] = ev.model_dump()
                    step.output_ref = ref
                step.status = "succeeded"
                step.actual_end = _ts()
                STORE.put(plan)
                trace_event(plan.id, "step.end", {"step_id": step.step_id, "status": step.status, "metrics": step.metrics, "output_ref": step.output_ref})
            except Exception as exc:  # pragma: no cover
                step.status = "failed"
                step.actual_end = _ts()
                step.metrics["error"] = str(exc)
                plan.status = "failed"
                plan.risks.append(f"Step {step.step_id} failed: {exc}")
                STORE.put(plan)
                trace_event(plan.id, "step.error", {"step_id": step.step_id, "error": str(exc)})
                return plan

        plan.status = "completed"
        STORE.put(plan)
        trace_event(plan.id, "plan.end", {"status": plan.status, "risks": plan.risks})
        return plan
