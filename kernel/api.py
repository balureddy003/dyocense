"""Lightweight REST layer for kernel services."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException

from kernel.datamodel import (
    OptiModel,
    PlanningContext,
    ScenarioSet,
    SKUContext,
    SupplierOption,
    scenario_set_from_dict,
    scenario_set_to_dict,
    optimodel_from_dict,
    optimodel_to_dict,
    solution_to_dict,
)
from kernel.forecast.service import ForecastService
from kernel.optiguide.service import OptiGuideService
from kernel.optimizer.service import OptimizerService
from kernel.pipeline import KernelPipeline, TenantContext

app = FastAPI(title="Dyocense Kernel API", version="0.1.0")

forecast_service = ForecastService()
optiguide_service = OptiGuideService()
optimizer_service = OptimizerService()
pipeline = KernelPipeline(
    forecast=forecast_service,
    optiguide=optiguide_service,
    optimizer=optimizer_service,
)


@app.post("/forecast/scenarios")
def forecast_scenarios(payload: Dict[str, Any]) -> Dict[str, Any]:
    context_data = payload.get("context")
    if not isinstance(context_data, dict):
        raise HTTPException(status_code=400, detail="context payload missing")
    context = _planning_context_from_dict(context_data)
    seed = payload.get("seed")
    scenario_set = forecast_service.generate(context, seed=seed)
    return scenario_set_to_dict(scenario_set)


@app.post("/forecast/feedback")
def forecast_feedback(payload: Dict[str, Any]) -> Dict[str, Any]:
    actuals = payload.get("actuals")
    if not isinstance(actuals, list) or not actuals:
        raise HTTPException(status_code=400, detail="actuals must be a non-empty list")
    by_sku: Dict[str, Dict[str, float]] = {}
    for entry in actuals:
        if not isinstance(entry, dict):
            continue
        sku = entry.get("sku")
        period = entry.get("period")
        quantity = entry.get("quantity")
        if not sku or period is None or quantity is None:
            continue
        sku_bank = by_sku.setdefault(str(sku), {})
        sku_bank[str(period)] = float(quantity)
    for sku, sku_actuals in by_sku.items():
        forecast_service.ingest_feedback(sku, sku_actuals)
    return {"status": "accepted", "updated_skus": list(by_sku.keys())}


@app.post("/optiguide/compile")
def compile_model(payload: Dict[str, Any]) -> Dict[str, Any]:
    goaldsl = payload.get("goal_dsl") or payload.get("goaldsl")
    context_data = payload.get("context")
    scenarios_data = payload.get("scenarios")
    if not isinstance(context_data, dict) or not isinstance(scenarios_data, dict):
        raise HTTPException(status_code=400, detail="context and scenarios required")
    context = _planning_context_from_dict(context_data)
    scenario_set = scenario_set_from_dict(scenarios_data)
    result = optiguide_service.compile(goaldsl, context, scenario_set)
    optimodel: OptiModel = result["optimodel"]
    hints = result["hints"]
    response = {
        "optimodel": optimodel_to_dict(optimodel),
        "hints": hints.__dict__,
        "metadata": result.get("metadata", {}),
        "compiled_inputs": result.get("compiled_inputs", {}),
    }
    if "policy_snapshot" in result:
        response["policy_snapshot"] = result["policy_snapshot"].__dict__
    return response


@app.post("/optimizer/solve")
def solve_model(payload: Dict[str, Any]) -> Dict[str, Any]:
    optimodel_data = payload.get("optimodel")
    compiled_inputs = payload.get("compiled_inputs") or {}
    context_data = payload.get("context")
    scenarios_data = payload.get("scenarios")
    if not isinstance(optimodel_data, dict) or not isinstance(context_data, dict) or not isinstance(scenarios_data, dict):
        raise HTTPException(status_code=400, detail="optimodel, context, and scenarios required")
    model = optimodel_from_dict(optimodel_data)
    context = _planning_context_from_dict(context_data)
    scenario_set = scenario_set_from_dict(scenarios_data)
    warm_start = payload.get("warm_start")
    result = optimizer_service.solve(model, compiled_inputs, context, scenario_set, warm_start=warm_start)
    solution_dict = solution_to_dict(result["solution"])
    return {"solution": solution_dict, "diagnostics": result.get("diagnostics", {})}


@app.post("/kernel/pipeline/run")
def run_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    goaldsl = payload.get("goal_dsl") or payload.get("goaldsl")
    context_data = payload.get("context")
    if not isinstance(context_data, dict):
        raise HTTPException(status_code=400, detail="context required")
    context = _planning_context_from_dict(context_data)
    seed = payload.get("seed")
    run_id = payload.get("run_id")
    warm_start = payload.get("warm_start")
    tenant_id = payload.get("tenant_id")
    tier = payload.get("tier")
    tenant_ctx = TenantContext(tenant_id=tenant_id, tier=tier) if tenant_id else None
    result = pipeline.run(
        goaldsl,
        context,
        seed=seed,
        run_id=run_id,
        warm_start=warm_start,
        tenant=tenant_ctx,
    )
    return result


def _planning_context_from_dict(payload: Dict[str, Any]) -> PlanningContext:
    try:
        horizon = int(payload.get("horizon", 0))
        periods = list(payload.get("periods", []))
        locations = list(payload.get("locations", ["default"]))
        skus_payload = payload["skus"]
    except (KeyError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid planning context: {exc}") from exc
    skus = []
    for sku_item in skus_payload:
        sku_name = sku_item.get("sku")
        if not sku_name:
            continue
        suppliers_payload = sku_item.get("supplier_options", [])
        supplier_options = []
        for supplier in suppliers_payload:
            supplier_options.append(
                SupplierOption(
                    supplier_id=supplier["supplier_id"],
                    price=float(supplier.get("price", 0.0)),
                    moq=int(supplier.get("moq", 0)),
                    lead_time_days=int(supplier.get("lead_time_days", 0)),
                    co2_per_unit=float(supplier.get("co2_per_unit", 0.0)),
                    capacity=supplier.get("capacity"),
                )
            )
        skus.append(
            SKUContext(
                sku=sku_name,
                demand_baseline=dict(sku_item.get("demand_baseline", {})),
                supplier_options=supplier_options,
            )
        )
    return PlanningContext(
        horizon=horizon or len(periods),
        periods=periods,
        locations=locations,
        skus=skus,
    )
