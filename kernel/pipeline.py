"""
End-to-end pipeline for Dyocense Decision Kernel
Implements: Forecast → OptiGuide → Optimizer → EvidenceGraph
See: kernel/KernelDESIGN.md
"""
from typing import Any
from kernel.forecast.service import ForecastService, ForecastConfig
from kernel.optiguide.service import OptiGuideService
from kernel.optimizer.service import OptimizerService
import importlib.util
import sys
import os

# Dynamically import evidence-graph/service.py as evidence_graph_service
evidence_graph_path = os.path.join(os.path.dirname(__file__), 'evidence-graph', 'service.py')
spec = importlib.util.spec_from_file_location('evidence_graph_service', evidence_graph_path)
evidence_graph_module = importlib.util.module_from_spec(spec)
sys.modules['evidence_graph_service'] = evidence_graph_module
spec.loader.exec_module(evidence_graph_module)
EvidenceGraphService = evidence_graph_module.EvidenceGraphService
from kernel.datamodel import PlanningContext

class KernelPipeline:
    def __init__(self):
        self.forecast = ForecastService()
        self.optiguide = OptiGuideService()
        self.optimizer = OptimizerService()
        self.evidence = EvidenceGraphService()

    def run(self, goaldsl: str, context: PlanningContext) -> dict:
        """
        Runs the full kernel pipeline as per design contract.
        Args:
            goaldsl: GoalDSL string
            context: PlanningContext object
        Returns:
            dict with evidence_ref and all intermediate results
        """
        # 1. Forecast
        scenario_set = self.forecast.generate(context)
        # 2. OptiGuide
        optiguide_result = self.optiguide.compile(goaldsl, context, scenario_set)
        # 3. Optimizer
        optimizer_result = self.optimizer.solve(optiguide_result["optimodel_ir"])
        # 4. Evidence Graph
        evidence_ref = self.evidence.persist(
            optimizer_result["solution"],
            optimizer_result["diagnostics"],
            scenario_ids=[s.id for s in scenario_set.scenarios],
            kpis=optimizer_result["diagnostics"].get("kpis", {})
        )
        return {
            "evidence_ref": evidence_ref,
            "forecast": scenario_set,
            "optimodel_ir": optiguide_result["optimodel_ir"],
            "optimizer_solution": optimizer_result["solution"],
            "diagnostics": optimizer_result["diagnostics"]
        }

if __name__ == "__main__":
    # Example usage: run pipeline with dummy GoalDSL and PlanningContext
    from kernel.datamodel import PlanningContext, SKUContext, SupplierOption

    # Dummy context setup
    context = PlanningContext(
        horizon=2,
        periods=["2025-09-01", "2025-09-02"],
        locations=["default"],
        skus=[
            SKUContext(
                sku="SKU1",
                demand_baseline={"2025-09-01": 100, "2025-09-02": 120},
                supplier_options=[
                    SupplierOption(supplier_id="SUP1", price=10.0, moq=1, lead_time_days=2, co2_per_unit=0.5),
                    SupplierOption(supplier_id="SUP2", price=11.0, moq=1, lead_time_days=3, co2_per_unit=0.6)
                ]
            ),
            SKUContext(
                sku="SKU2",
                demand_baseline={"2025-09-01": 80, "2025-09-02": 90},
                supplier_options=[
                    SupplierOption(supplier_id="SUP3", price=9.5, moq=1, lead_time_days=1, co2_per_unit=0.4)
                ]
            )
        ]
    )
    goaldsl = "minimize cost subject to service >= 97%"

    pipeline = KernelPipeline()
    result = pipeline.run(goaldsl, context)
    print("Evidence Ref:", result["evidence_ref"])
    print("Forecast Stats:", result["forecast"].stats)
    print("Optimizer Solution:", result["optimizer_solution"])
    print("Diagnostics:", result["diagnostics"])
