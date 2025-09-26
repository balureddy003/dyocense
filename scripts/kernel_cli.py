#!/usr/bin/env python3
"""CLI for interacting with kernel services (forecast, compile, solve, evidence)."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

evidence_graph_path = PROJECT_ROOT / "kernel" / "evidence-graph" / "service.py"
spec = importlib.util.spec_from_file_location("cli_evidence_graph_service", evidence_graph_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore[union-attr]
EvidenceGraphService = module.EvidenceGraphService
from kernel.datamodel import PlanningContext, SKUContext, SupplierOption, scenario_set_to_dict
from kernel.domain import get_adapter
from kernel.forecast.service import ForecastConfig, ForecastService
from kernel.optiguide.service import OptiGuideService
from kernel.optimizer.service import OptimizerService
from kernel.pipeline import KernelPipeline, TenantContext
from kernel.multitenant.scheduler import TenantScheduler, TierConfig, TenantBudget
from kernel.datamodel import scenario_set_to_dict


def load_json(path: Path | None, default: Any = None) -> Any:
    if path is None:
        return default
    return json.loads(Path(path).read_text(encoding="utf-8"))


def context_from_json(payload: Dict[str, Any]) -> PlanningContext:
    if "context" in payload and "skus" not in payload:
        payload = payload["context"]
    skus = []
    for sku_ctx in payload.get("skus", []):
        suppliers = [
            SupplierOption(
                supplier_id=opt["supplier_id"],
                price=opt["price"],
                moq=opt.get("moq", 1),
                lead_time_days=opt.get("lead_time_days", 1),
                co2_per_unit=opt.get("co2_per_unit", 0.0),
                capacity=opt.get("capacity"),
            )
            for opt in sku_ctx.get("supplier_options", [])
        ]
        skus.append(
            SKUContext(
                sku=sku_ctx["sku"],
                demand_baseline=sku_ctx["demand_baseline"],
                supplier_options=suppliers,
            )
        )
    return PlanningContext(
        horizon=payload["horizon"],
        periods=payload["periods"],
        locations=payload.get("locations", []),
        skus=skus,
    )


def build_pipeline(domain: str | None, tenant_scheduler: TenantScheduler | None) -> KernelPipeline:
    adapter = get_adapter(domain)
    return KernelPipeline(
        forecast=ForecastService(config=ForecastConfig()),
        optiguide=OptiGuideService(),
        optimizer=OptimizerService(),
        evidence=EvidenceGraphService(),
        domain_adapter=adapter,
        scheduler=tenant_scheduler,
    )


def init_scheduler(tenant_config: Dict[str, Any] | None) -> TenantScheduler | None:
    if not tenant_config:
        return None
    scheduler = TenantScheduler()
    for tier_name, cfg in tenant_config.get("tiers", {}).items():
        scheduler.register_tier(
            TierConfig(
                name=tier_name,
                weight=cfg.get("weight", 1),
                rate_limit_per_minute=cfg.get("rate_limit_per_minute", 60),
                default_budget=TenantBudget(
                    solver_sec=cfg.get("budget", {}).get("solver_sec", 10.0),
                    gpu_sec=cfg.get("budget", {}).get("gpu_sec", 0.0),
                    llm_tokens=cfg.get("budget", {}).get("llm_tokens", 1_000_000.0),
                ),
            )
        )
    return scheduler


def forecast_command(args: argparse.Namespace) -> None:
    context_data = load_json(Path(args.context))
    context = context_from_json(context_data)
    service = ForecastService()
    scenario_set = service.generate(context, seed=args.seed)
    print(json.dumps(scenario_set_to_dict(scenario_set), indent=2, default=str))


def pipeline_command(args: argparse.Namespace) -> None:
    context_data = load_json(Path(args.context))
    context = context_from_json(context_data)
    goal_data = load_json(Path(args.goal))
    feedback_data = load_json(Path(args.feedback)) if args.feedback else None
    tenant_config = load_json(Path(args.scheduler_config)) if args.scheduler_config else None
    scheduler = init_scheduler(tenant_config)
    pipeline = build_pipeline(args.domain, scheduler)
    tenant = TenantContext(args.tenant_id, args.tier) if args.tenant_id and args.tier else None

    if feedback_data:
        for sku, actuals in feedback_data.get("actuals", {}).items():
            pipeline.forecast.ingest_feedback(sku, actuals)

    if args.mode == "compile":
        scenarios = load_json(Path(args.scenarios))
        result = pipeline.optiguide.compile(goal_data, context, scenarios)
    elif args.mode == "solve":
        scenarios = load_json(Path(args.scenarios))
        optiguide_result = pipeline.optiguide.compile(goal_data, context, scenarios)
        result = pipeline.optimizer.solve(
            optiguide_result["optimodel"],
            optiguide_result["compiled_inputs"],
            context,
            scenarios,
            warm_start=load_json(Path(args.warm_start)) if args.warm_start else None,
        )
    elif args.mode == "run":
        result = pipeline.run(
            goal_data,
            context,
            seed=args.seed,
            run_id=args.run_id,
            tenant=tenant,
        )
    elif args.mode == "counterfactual":
        if not args.sku or not args.block_supplier:
            raise SystemExit("--sku and --block-supplier are required for counterfactual mode")
        result = pipeline.supplier_counterfactual(
            goal_data,
            context,
            sku=args.sku,
            block_supplier=args.block_supplier,
            seed=args.seed,
            run_id=args.run_id,
            tenant=tenant,
        )
    else:
        raise ValueError("Unknown mode")
    print(json.dumps(result, indent=2, default=str))


def evidence_command(args: argparse.Namespace) -> None:
    payload = load_json(Path(args.payload))
    service = EvidenceGraphService()
    ref = service.persist(
        payload["optimodel"],
        payload["solution"],
        payload["scenarios"],
        payload.get("hints"),
        metadata=payload.get("metadata"),
    )
    print(json.dumps({"evidence_ref": ref.uri, "snapshot_hash": ref.snapshot_hash}, indent=2))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Kernel CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    forecast_p = sub.add_parser("forecast")
    forecast_p.add_argument("--context", required=True)
    forecast_p.add_argument("--seed", type=int, default=None)
    forecast_p.set_defaults(func=forecast_command)

    pipeline_p = sub.add_parser("pipeline")
    pipeline_p.add_argument("--mode", choices=["compile", "solve", "run", "counterfactual"], required=True)
    pipeline_p.add_argument("--context", required=True)
    pipeline_p.add_argument("--goal", required=True)
    pipeline_p.add_argument("--scenarios")
    pipeline_p.add_argument("--warm-start")
    pipeline_p.add_argument("--seed", type=int)
    pipeline_p.add_argument("--run-id")
    pipeline_p.add_argument("--tenant-id")
    pipeline_p.add_argument("--tier")
    pipeline_p.add_argument("--domain")
    pipeline_p.add_argument("--scheduler-config")
    pipeline_p.add_argument("--sku")
    pipeline_p.add_argument("--block-supplier")
    pipeline_p.add_argument("--feedback")
    pipeline_p.set_defaults(func=pipeline_command)

    evidence_p = sub.add_parser("evidence")
    evidence_p.add_argument("--payload", required=True)
    evidence_p.set_defaults(func=evidence_command)

    args = parser.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    from kernel.datamodel import scenario_set_to_dict

    raise SystemExit(main(sys.argv[1:]))
