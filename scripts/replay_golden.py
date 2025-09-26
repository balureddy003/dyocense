#!/usr/bin/env python3
"""Replay golden data pack through the kernel pipeline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kernel.datamodel import PlanningContext, SKUContext, SupplierOption
from kernel.domain import (
    HealthcareDomainAdapter,
    HospitalityDomainAdapter,
    LogisticsDomainAdapter,
    ManufacturingDomainAdapter,
    RetailDomainAdapter,
)
from kernel.forecast.service import ForecastConfig, ForecastService
from kernel.optiguide.service import OptiGuideService
from kernel.optimizer.service import OptimizerService
from kernel.pipeline import KernelPipeline
from evidence_graph_service import EvidenceGraphService

DOMAIN_ADAPTERS = {
    "retail": RetailDomainAdapter(),
    "manufacturing": ManufacturingDomainAdapter(),
    "healthcare": HealthcareDomainAdapter(),
    "logistics": LogisticsDomainAdapter(),
    "hospitality": HospitalityDomainAdapter(),
}


def load_pack(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def context_from_payload(payload: dict) -> PlanningContext:
    skus = []
    for sku_ctx in payload["skus"]:
        suppliers = [
            SupplierOption(
                supplier_id=opt["supplier_id"],
                price=opt["price"],
                moq=opt.get("moq", 1),
                lead_time_days=opt.get("lead_time_days", 1),
                co2_per_unit=opt.get("co2_per_unit", 0.0),
                capacity=opt.get("capacity"),
            )
            for opt in sku_ctx["supplier_options"]
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
        locations=payload["locations"],
        skus=skus,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Replay golden data pack")
    parser.add_argument("pack", type=Path, help="Path to golden pack JSON")
    parser.add_argument(
        "--domain",
        choices=DOMAIN_ADAPTERS.keys(),
        help="Domain adapter to apply (overrides pack)"
    )
    parser.add_argument("--seed", type=int, help="Override RNG seed", default=None)
    args = parser.parse_args(argv)

    pack = load_pack(args.pack)
    domain_name = args.domain or pack.get("domain")
    adapter = DOMAIN_ADAPTERS.get(domain_name) if domain_name else None

    context = context_from_payload(pack["context"])
    forecast = ForecastService(config=ForecastConfig())
    pipeline = KernelPipeline(
        forecast=forecast,
        optiguide=OptiGuideService(),
        optimizer=OptimizerService(),
        evidence=EvidenceGraphService(),
        domain_adapter=adapter,
    )

    result = pipeline.run(
        pack["goal"],
        context,
        seed=args.seed or pack.get("seed"),
        run_id=f"replay-{args.pack.stem}",
    )
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
