"""Golden run regression tests using domain adapters."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kernel.datamodel import PlanningContext, SKUContext, SupplierOption
from kernel.domain import ManufacturingDomainAdapter, RetailDomainAdapter
from kernel.forecast.service import ForecastConfig, ForecastService
from kernel.optiguide.service import OptiGuideService
from kernel.optimizer.service import OptimizerService
from kernel.pipeline import KernelPipeline
from evidence_graph_service import EvidenceGraphService


def load_pack(name: str) -> dict:
    base = PROJECT_ROOT / "tests" / "data" / "golden"
    return json.loads((base / name).read_text(encoding="utf-8"))


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


class GoldenRunTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _pipeline(self, adapter) -> KernelPipeline:
        return KernelPipeline(
            forecast=ForecastService(config=ForecastConfig(cache_dir=self.tmp_path / "cache")),
            optiguide=OptiGuideService(),
            optimizer=OptimizerService(),
            evidence=EvidenceGraphService(data_root=self.tmp_path / "evidence"),
            domain_adapter=adapter,
        )

    def test_retail_golden_run(self) -> None:
        pack = load_pack("small_retail.json")
        expected = load_pack("retail_result.json")
        pipeline = self._pipeline(RetailDomainAdapter())
        context = context_from_payload(pack["context"])
        result = pipeline.run(pack["goal"], context, seed=pack["seed"], run_id="golden-retail")
        kpis = result["solution"]["kpis"]
        self.assertAlmostEqual(kpis["total_cost"], expected["kpis"]["total_cost"], places=2)
        self.assertAlmostEqual(kpis["service_level"], expected["kpis"]["service_level"], places=3)
        self.assertEqual(result["solution"]["binding_constraints"], expected["binding_constraints"])
        worst_case = result["diagnostics"]["stress_test"]["worst_case_service"]
        self.assertAlmostEqual(worst_case, expected["worst_case_service"], places=3)
        self.assertIsNotNone(result.get("optimodel_sha"))
        self.assertIsNotNone(result.get("plan_dna"))

    def test_manufacturing_golden_run(self) -> None:
        pack = load_pack("small_manufacturing.json")
        expected = load_pack("manufacturing_result.json")
        pipeline = self._pipeline(ManufacturingDomainAdapter())
        context = context_from_payload(pack["context"])
        result = pipeline.run(pack["goal"], context, seed=pack["seed"], run_id="golden-mfg")
        kpis = result["solution"]["kpis"]
        self.assertAlmostEqual(kpis["total_cost"], expected["kpis"]["total_cost"], places=2)
        self.assertAlmostEqual(kpis["service_level"], expected["kpis"]["service_level"], places=3)
        self.assertEqual(result["solution"]["binding_constraints"], expected["binding_constraints"])
        setup_runs = result["diagnostics"].get("domain", {}).get("setup_runs")
        self.assertEqual(setup_runs, expected["setup_runs"])
        self.assertIsNotNone(result.get("optimodel_sha"))
        self.assertIsNotNone(result.get("plan_dna"))


if __name__ == "__main__":
    unittest.main()
