"""Unit tests for the kernel pipeline using the built-in unittest framework."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
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
from kernel.optimizer.service import OptimizerConfig, OptimizerService
from kernel.multitenant.scheduler import (
    BudgetExceeded,
    CostEstimate,
    RateLimitExceeded,
    TenantBudget,
    TenantScheduler,
    TierConfig,
)
from kernel.pipeline import KernelPipeline, TenantContext


def _load_evidence_graph_service() -> type:
    service_path = PROJECT_ROOT / "kernel" / "evidence-graph" / "service.py"
    spec = importlib.util.spec_from_file_location("tests_evidence_graph_service", service_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to locate EvidenceGraphService module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.EvidenceGraphService  # type: ignore[attr-defined]


EvidenceGraphService = _load_evidence_graph_service()


def build_planning_context() -> PlanningContext:
    return PlanningContext(
        horizon=2,
        periods=["2025-09-01", "2025-09-02"],
        locations=["default"],
        skus=[
            SKUContext(
                sku="SKU1",
                demand_baseline={"2025-09-01": 100, "2025-09-02": 120},
                supplier_options=[
                    SupplierOption(
                        supplier_id="SUP1",
                        price=10.0,
                        moq=10,
                        lead_time_days=2,
                        co2_per_unit=0.5,
                    ),
                    SupplierOption(
                        supplier_id="SUP2",
                        price=11.0,
                        moq=5,
                        lead_time_days=3,
                        co2_per_unit=0.6,
                    ),
                ],
            ),
            SKUContext(
                sku="SKU2",
                demand_baseline={"2025-09-01": 80, "2025-09-02": 90},
                supplier_options=[
                    SupplierOption(
                        supplier_id="SUP3",
                        price=9.5,
                        moq=1,
                        lead_time_days=1,
                        co2_per_unit=0.4,
                    ),
                ],
            ),
        ],
    )


def build_pipeline(tmp_path: Path, *, quantile: float = 0.95) -> KernelPipeline:
    forecast_service = ForecastService(
        config=ForecastConfig(cache_dir=tmp_path / "forecast-cache")
    )
    evidence_service = EvidenceGraphService(data_root=tmp_path / "evidence")
    optimizer = OptimizerService(config=OptimizerConfig(service_quantile=quantile))
    return KernelPipeline(
        forecast=forecast_service,
        optiguide=OptiGuideService(),
        optimizer=optimizer,
        evidence=evidence_service,
    )


class ForecastServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.service = ForecastService(
            config=ForecastConfig(cache_dir=self.tmp_path / "forecast-cache")
        )
        self.context = build_planning_context()

    def tearDown(self) -> None:
        self.tmp.cleanup()
        for path in (Path("kernel/forecast/.cache"),):
            if path.exists():
                shutil.rmtree(path)

    def test_stats_include_summary_metrics(self) -> None:
        scenario_set = self.service.generate(self.context, seed=2025)
        stats = scenario_set.stats.get("SKU1", {})
        self.assertIn("mean", stats)
        self.assertIn("sigma", stats)
        self.assertIn("p95", stats)
        self.assertIn("conformal_lower", stats)
        self.assertIn("conformal_upper", stats)
        backtest = self.service.last_run_info.get("backtest", {})
        self.assertIsInstance(backtest, dict)

    def test_fallback_triggered_for_insufficient_history(self) -> None:
        sparse_context = PlanningContext(
            horizon=self.context.horizon,
            periods=self.context.periods,
            locations=self.context.locations,
            skus=[
                SKUContext(
                    sku="SKUX",
                    demand_baseline={"2025-09-01": 100.0, "2025-09-02": 0.0},
                    supplier_options=self.context.skus[0].supplier_options,
                )
            ],
        )
        self.service.generate(sparse_context, seed=555)
        self.assertIn("SKUX", self.service.last_run_info.get("fallback_skus", []))

    def test_cache_metrics_increment(self) -> None:
        self.service.generate(self.context, seed=101)
        self.service.generate(self.context, seed=101)
        self.assertGreaterEqual(self.service.metrics.get("cache_hits", 0.0), 1.0)

    def test_feedback_ingestion_updates_summary(self) -> None:
        self.service.ingest_feedback("SKU1", {"2025-09-03": 130, "2025-09-04": 125})
        scenario_set = self.service.generate(self.context, seed=2026)
        feedback = self.service.last_run_info.get("feedback", {})
        self.assertIn("SKU1", feedback)
        self.assertGreater(feedback["SKU1"]["avg_actual"], 0)


class KernelPipelineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.context = build_planning_context()

    def tearDown(self) -> None:
        self.tmp.cleanup()
        # Ensure any default cache directories created during tests are removed
        for path in (Path("kernel/forecast/.cache"), Path("kernel/evidence-graph/data")):
            if path.exists():
                shutil.rmtree(path)

    def test_uc_ker_001_goal_to_plan(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 0.7, "service": 0.2, "co2": 0.1},
            "constraints": {"budget_month": 8000, "service_min": 0.95},
            "policies": {"vendor_blocklist": []},
        }

        result_a = pipeline.run(goaldsl, self.context, seed=12345, run_id="uc-ker-001")
        result_b = pipeline.run(goaldsl, self.context, seed=12345, run_id="uc-ker-001")

        for result in (result_a, result_b):
            solution = result["solution"]
            self.assertIn(solution["status"], {"FEASIBLE", "OPTIMAL"})
            self.assertTrue(solution["steps"], "Expected non-empty plan steps")
            self.assertTrue(solution["binding_constraints"], "Binding constraints required")
            self.assertTrue(result["evidence_ref"].startswith("evidence://"))
            llm_summary = result.get("llm_summary")
            self.assertIsInstance(llm_summary, dict)
            self.assertIn("text", llm_summary)
            self.assertEqual(llm_summary.get("source"), "fallback")

        self.assertEqual(result_a["solution"]["kpis"], result_b["solution"]["kpis"])
        self.assertEqual(result_a["solution"]["steps"], result_b["solution"]["steps"])
        self.assertIsNotNone(result_a.get("optimodel_sha"))
        self.assertIsNotNone(result_a.get("plan_dna"))

    def test_pipeline_respects_vendor_blocklist(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {"budget_month": 10_000, "service_min": 0.5},
            "policies": {"vendor_blocklist": ["SUP1"]},
        }

        result = pipeline.run(goaldsl, self.context, seed=9876, run_id="vendor-block")
        suppliers = {step["supplier"] for step in result["solution"]["steps"]}
        self.assertTrue({"SUP1"}.isdisjoint(suppliers))

    def test_optimizer_auto_relax_resolves_capacity_shortage(self) -> None:
        constrained_context = PlanningContext(
            horizon=self.context.horizon,
            periods=self.context.periods,
            locations=self.context.locations,
            skus=[
                SKUContext(
                    sku="SKU1",
                    demand_baseline={"2025-09-01": 150, "2025-09-02": 150},
                    supplier_options=[
                        SupplierOption(
                            supplier_id="SUP1",
                            price=10.0,
                            moq=10,
                            lead_time_days=2,
                            co2_per_unit=0.5,
                            capacity=50,
                        ),
                    ],
                )
            ],
        )

        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {"budget_month": 20_000, "service_min": 0.99},
            "policies": {},
        }

        result = pipeline.run(goaldsl, constrained_context, seed=13579, run_id="capacity-short")
        self.assertEqual(result["solution"]["status"], "FEASIBLE_RELAXED")
        self.assertIn("capacity_relaxed", result["solution"]["binding_constraints"])
        relaxation = result["diagnostics"].get("relaxation")
        self.assertIsNotNone(relaxation)
        self.assertEqual(relaxation.get("status"), "APPLIED")
        self.assertTrue(relaxation.get("adjustments"))

    def test_optimizer_reduction_and_stress_outputs(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {
                "budget_month": 10_000,
                "scenario_reduction": {"k": 1},
                "lns_iterations": 2,
            },
            "policies": {},
        }

        result = pipeline.run(goaldsl, self.context, seed=2468, run_id="reduction-test")
        diagnostics = result["diagnostics"]
        reduction = diagnostics.get("reduction", {})
        self.assertLess(reduction.get("reduced_count", 0), reduction.get("original_count", 0))
        stress = diagnostics.get("stress_test", {})
        self.assertIn("worst_case_service", stress)
        lns_diag = diagnostics.get("lns", {})
        self.assertIsNotNone(lns_diag)
        self.assertIn("iterations_requested", lns_diag)
        self.assertTrue(diagnostics.get("warm_start") is False)
        robust_eval = diagnostics.get("robust_eval", {})
        self.assertIn("cvar_cost", robust_eval)

    def test_optimizer_default_reduction_and_lns(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 10_000}, "policies": {}}
        result = pipeline.run(goaldsl, self.context, seed=7777, run_id="default-reduction")
        diagnostics = result["diagnostics"]
        reduction = diagnostics.get("reduction", {})
        self.assertLess(reduction.get("reduced_count", 0), reduction.get("original_count", 0))
        lns_diag = diagnostics.get("lns")
        self.assertIsNotNone(lns_diag)

    def test_delta_solve_returns_kpi_deltas(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {"budget_month": 10_000},
            "policies": {},
        }
        modifications = {
            "constraints": {"budget_month": 8_000},
            "context": {"remove_suppliers": {"SKU1": ["SUP1"]}},
        }
        result = pipeline.delta_solve(
            goaldsl,
            self.context,
            modifications,
            seed=1122,
            run_id="delta-test",
        )
        self.assertIn("baseline", result)
        self.assertIn("modified", result)
        self.assertIn("kpi_deltas", result)
        delta_cost = result["kpi_deltas"].get("total_cost")
        self.assertIsNotNone(delta_cost)
        self.assertNotEqual(delta_cost, 0.0)
        self.assertTrue(result["modified"]["diagnostics"].get("warm_start"))

    def test_supplier_counterfactual_blocks_supplier(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {"budget_month": 10_000},
            "policies": {},
        }
        cf = pipeline.supplier_counterfactual(
            goaldsl,
            self.context,
            sku="SKU1",
            block_supplier="SUP1",
            seed=2211,
            run_id="cf-test",
        )
        suppliers_cf = {step["supplier"] for step in cf["modified"]["solution"]["steps"]}
        self.assertNotIn("SUP1", suppliers_cf)
        self.assertIn("baseline", cf)
        self.assertIn("kpi_deltas", cf)

    def test_policy_snapshot_present_in_result(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {"budget_month": 10_000, "service_min": 0.9},
            "policies": {},
        }
        result = pipeline.run(goaldsl, self.context, seed=3141, run_id="policy-ok")
        policy = result.get("policy")
        self.assertIsNotNone(policy)
        self.assertTrue(policy["allow"])
        self.assertIn("controls", policy)

    def test_policy_guard_budget_cap_post_run(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {},
            "policies": {"caps": {"max_budget": 2_000}},
        }
        result = pipeline.run(goaldsl, self.context, seed=5150, run_id="policy-cap")
        policy = result["policy"]
        self.assertFalse(policy["allow"])
        self.assertTrue(any("total_cost" in reason for reason in policy["reasons"]))

    def test_policy_guard_enforces_tier_scenario_cap(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {"budget_month": 10_000},
            "policies": {},
        }
        tenant = TenantContext(tenant_id="tenant-free", tier="free")
        with self.assertRaises(ValueError) as ctx:
            pipeline.run(goaldsl, self.context, seed=42424, tenant=tenant)
        self.assertIn("scenario count", str(ctx.exception))

    def test_simulation_diagnostics_available(self) -> None:
        pipeline = build_pipeline(self.tmp_path)
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {"budget_month": 10_000, "service_min": 0.9},
            "policies": {},
        }
        result = pipeline.run(goaldsl, self.context, seed=2024, run_id="simulation-check")
        diagnostics = result["diagnostics"]
        simulation = diagnostics.get("simulation")
        self.assertIsNotNone(simulation)
        self.assertIn("mean_service", simulation)
        self.assertLessEqual(simulation["mean_service"], 1.0)
        self.assertGreaterEqual(simulation["mean_service"], 0.0)


class EvidenceGraphServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.context = build_planning_context()
        forecast = ForecastService(
            config=ForecastConfig(cache_dir=self.tmp_path / "forecast-cache")
        )
        self.scenarios = forecast.generate(self.context, seed=999)
        self.service = EvidenceGraphService(data_root=self.tmp_path / "evidence")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_persist_writes_snapshot_and_graph(self) -> None:
        optiguide = OptiGuideService()
        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 8000}, "policies": {}}
        compiled = optiguide.compile(goaldsl, self.context, self.scenarios)
        optimizer = OptimizerService()
        solve_result = optimizer.solve(
            compiled["optimodel"],
            compiled["compiled_inputs"],
            self.context,
            self.scenarios,
        )
        evidence_ref = self.service.persist(
            compiled["optimodel"],
            solve_result["solution"],
            self.scenarios,
            compiled["hints"],
            metadata={},
        )
        self.assertTrue(evidence_ref.uri.startswith("evidence://"))
        snapshot_path = self.service.snapshot_dir / f"{evidence_ref.snapshot_hash}.json"
        self.assertTrue(snapshot_path.exists())
        graph_lines = self.service.graph_log.read_text(encoding="utf-8").strip().splitlines()
        self.assertTrue(graph_lines)
        graph_event = json.loads(graph_lines[-1])
        self.assertIn("nodes", graph_event)
        self.assertIn("edges", graph_event)

    def test_persist_queues_when_unavailable(self) -> None:
        offline_service = EvidenceGraphService(data_root=self.tmp_path / "offline", available=False)
        optiguide = OptiGuideService()
        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 8000}, "policies": {}}
        compiled = optiguide.compile(goaldsl, self.context, self.scenarios)
        optimizer = OptimizerService()
        solve_result = optimizer.solve(
            compiled["optimodel"],
            compiled["compiled_inputs"],
            self.context,
            self.scenarios,
        )
        offline_service.persist(
            compiled["optimodel"],
            solve_result["solution"],
            self.scenarios,
            compiled["hints"],
            metadata={},
        )
        queue_lines = offline_service.queue_file.read_text(encoding="utf-8").strip().splitlines()
        self.assertTrue(queue_lines)
        last_status = offline_service.last_status
        self.assertTrue(last_status.get("queued"))

    def test_evidence_gc_and_redaction(self) -> None:
        service = EvidenceGraphService(data_root=self.tmp_path / "gc-test", max_snapshots=1)
        optiguide = OptiGuideService()
        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 8000}, "policies": {}}
        compiled = optiguide.compile(goaldsl, self.context, self.scenarios)
        optimizer = OptimizerService()
        solve_result = optimizer.solve(
            compiled["optimodel"],
            compiled["compiled_inputs"],
            self.context,
            self.scenarios,
        )
        for idx in range(2):
            service.persist(
                compiled["optimodel"],
                solve_result["solution"],
                self.scenarios,
                compiled["hints"],
                metadata={"run_id": f"gc-{idx}", "user_email": "secret@example.com"},
            )
        snapshots = list(service.snapshot_dir.glob("*.json"))
        self.assertLessEqual(len(snapshots), 1)
        if snapshots:
            payload = json.loads(snapshots[0].read_text("utf-8"))
            self.assertNotIn("user_email", payload.get("metadata", {}))

    def test_query_supplier_explanation_returns_path_and_counterfactual(self) -> None:
        pipeline = KernelPipeline(
            forecast=ForecastService(
                config=ForecastConfig(cache_dir=self.tmp_path / "forecast-cache2")
            ),
            optiguide=OptiGuideService(),
            optimizer=OptimizerService(),
            evidence=self.service,
        )
        goaldsl = {
            "objective": {"cost": 0.7, "service": 0.3},
            "constraints": {"budget_month": 9000},
            "policies": {},
        }
        pipeline.run(goaldsl, self.context, seed=777, run_id="explain-test")
        plan_id = self.service.last_status.get("plan_id")
        self.assertIsNotNone(plan_id)
        explanation = self.service.query_supplier_explanation(plan_id, "SUP1")
        path = explanation["path"]
        self.assertTrue(any(node.startswith("step::") for node in path))
        self.assertTrue(any(node.startswith("datasource::") for node in path))
        counterfactual = explanation["counterfactual"]
        self.assertIn("available", counterfactual)


class TenantSchedulerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.scheduler = TenantScheduler()
        self.scheduler.register_tier(
            TierConfig(
                name="standard",
                weight=1,
                rate_limit_per_minute=1,
                default_budget=TenantBudget(2.0, 0.0, 1000.0),
            )
        )
        self.scheduler.register_tier(
            TierConfig(
                name="premium",
                weight=3,
                rate_limit_per_minute=3,
                default_budget=TenantBudget(5.0, 0.0, 1000.0),
            )
        )
        self.context = build_planning_context()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _pipeline(self, scheduler: TenantScheduler) -> KernelPipeline:
        return KernelPipeline(
            forecast=ForecastService(
                config=ForecastConfig(cache_dir=self.tmp_path / "cache")
            ),
            optiguide=OptiGuideService(),
            optimizer=OptimizerService(),
            evidence=EvidenceGraphService(data_root=self.tmp_path / "ev"),
            domain_adapter=None,
            scheduler=scheduler,
        )

    def test_rate_limit_enforced(self) -> None:
        pipeline = self._pipeline(self.scheduler)
        tenant = TenantContext(tenant_id="tenant-a", tier="standard")
        context = build_planning_context()
        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 9000}, "policies": {}}
        pipeline.run(goaldsl, self.context, tenant=tenant, seed=100)
        with self.assertRaises(RateLimitExceeded):
            pipeline.run(goaldsl, self.context, tenant=tenant, seed=101)

    def test_budget_consumption(self) -> None:
        scheduler = TenantScheduler()
        scheduler.register_tier(
            TierConfig(
                name="tight",
                weight=1,
                rate_limit_per_minute=10,
                default_budget=TenantBudget(3.0, 0.0, 1000.0),
            )
        )
        pipeline = self._pipeline(scheduler)
        tenant = TenantContext("tenant-b", "tight")
        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 9000}, "policies": {}}
        pipeline.run(goaldsl, self.context, tenant=tenant, seed=200)
        scheduler._states[tenant.tenant_id].remaining.solver_sec = 0.1
        with self.assertRaises(BudgetExceeded):
            pipeline.run(goaldsl, self.context, tenant=tenant, seed=201)

    def test_weighted_fairness(self) -> None:
        state_before = {}
        lease_a = self.scheduler.acquire("tenantA", "standard", CostEstimate(solver_sec=1.0))
        lease_a.complete(CostEstimate(solver_sec=1.0))
        lease_b = self.scheduler.acquire("tenantB", "premium", CostEstimate(solver_sec=1.0))
        lease_b.complete(CostEstimate(solver_sec=1.0))
        va = self.scheduler._states["tenantA"].virtual_finish
        vb = self.scheduler._states["tenantB"].virtual_finish
        self.assertLess(vb, va)

    def test_retail_domain_adapter_modifies_goal_and_postprocess(self) -> None:
        adapter = RetailDomainAdapter()
        pipeline = KernelPipeline(
            forecast=ForecastService(
                config=ForecastConfig(cache_dir=self.tmp_path / "retail-cache")
            ),
            optiguide=OptiGuideService(),
            optimizer=OptimizerService(),
            evidence=EvidenceGraphService(data_root=self.tmp_path / "retail-evidence"),
            domain_adapter=adapter,
        )

        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 9000}, "policies": {}}
        result = pipeline.run(goaldsl, self.context, seed=4321, run_id="retail-test")
        diagnostics = result.get("diagnostics", {})
        domain_diag = diagnostics.get("domain", {})
        self.assertIn("estimated_waste", domain_diag)

    def test_manufacturing_domain_adapter_applies_constraints(self) -> None:
        adapter = ManufacturingDomainAdapter()
        pipeline = KernelPipeline(
            forecast=ForecastService(
                config=ForecastConfig(cache_dir=self.tmp_path / "mfg-cache")
            ),
            optiguide=OptiGuideService(),
            optimizer=OptimizerService(),
            evidence=EvidenceGraphService(data_root=self.tmp_path / "mfg-evidence"),
            domain_adapter=adapter,
        )

        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 9000}, "policies": {}}
        result = pipeline.run(goaldsl, self.context, seed=1234, run_id="mfg-test")
        diagnostics = result.get("diagnostics", {}).get("domain", {})
        self.assertIn("setup_runs", diagnostics)

    def test_healthcare_domain_adapter_annotations(self) -> None:
        adapter = HealthcareDomainAdapter()
        pipeline = KernelPipeline(
            forecast=ForecastService(
                config=ForecastConfig(cache_dir=self.tmp_path / "health-cache")
            ),
            optiguide=OptiGuideService(),
            optimizer=OptimizerService(),
            evidence=EvidenceGraphService(data_root=self.tmp_path / "health-evidence"),
            domain_adapter=adapter,
        )

        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 7000}, "policies": {}}
        result = pipeline.run(goaldsl, self.context, seed=5555, run_id="health-test")
        diagnostics = result.get("diagnostics", {}).get("domain", {})
        self.assertIn("on_call_shifts", diagnostics)

    def test_logistics_domain_adapter_annotations(self) -> None:
        adapter = LogisticsDomainAdapter()
        pipeline = KernelPipeline(
            forecast=ForecastService(
                config=ForecastConfig(cache_dir=self.tmp_path / "logistics-cache")
            ),
            optiguide=OptiGuideService(),
            optimizer=OptimizerService(),
            evidence=EvidenceGraphService(data_root=self.tmp_path / "logistics-evidence"),
            domain_adapter=adapter,
        )

        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 9500}, "policies": {}}
        result = pipeline.run(goaldsl, self.context, seed=2222, run_id="logistics-test")
        diagnostics = result.get("diagnostics", {}).get("domain", {})
        self.assertIn("route_segments", diagnostics)

    def test_hospitality_domain_adapter_annotations(self) -> None:
        adapter = HospitalityDomainAdapter()
        pipeline = KernelPipeline(
            forecast=ForecastService(
                config=ForecastConfig(cache_dir=self.tmp_path / "hospitality-cache")
            ),
            optiguide=OptiGuideService(),
            optimizer=OptimizerService(),
            evidence=EvidenceGraphService(data_root=self.tmp_path / "hospitality-evidence"),
            domain_adapter=adapter,
        )

        goaldsl = {"objective": {"cost": 1.0}, "constraints": {"budget_month": 8000}, "policies": {}}
        result = pipeline.run(goaldsl, self.context, seed=3333, run_id="hospitality-test")
        diagnostics = result.get("diagnostics", {}).get("domain", {})
        self.assertIn("freshness_score", diagnostics)

class OptiGuideServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.context = build_planning_context()
        self.scenario_set = ForecastService(
            config=ForecastConfig(cache_dir=self.tmp_path / "forecast-cache")
        ).generate(self.context, seed=77)
        self.service = OptiGuideService()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _compile_with_mode(self, mode: str) -> str:
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {
                "budget_month": 8000,
                "robust": {"mode": mode},
            },
            "policies": {},
        }
        result = self.service.compile(goaldsl, self.context, self.scenario_set)
        return result["optimodel"].robust.aggregation  # type: ignore[return-value]

    def test_compile_supports_robust_modes(self) -> None:
        mapping = {
            "p95": "p95",
            "dro_wasserstein": "cvar",
            "conformal": "quantile_interval",
        }
        for mode, expected in mapping.items():
            aggregation = self._compile_with_mode(mode)
            self.assertEqual(aggregation, expected)

    def test_policy_denial_raises_error(self) -> None:
        goaldsl = {
            "objective": {"cost": 1.0},
            "constraints": {"budget_month": 5000},
            "policies": {"deny": True, "deny_reasons": ["cap exceeded"], "policy_id": "opa-123"},
        }
        with self.assertRaises(ValueError) as ctx:
            self.service.compile(goaldsl, self.context, self.scenario_set)
        self.assertIn("cap exceeded", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
