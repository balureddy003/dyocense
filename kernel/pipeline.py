"""End-to-end pipeline orchestrating Forecast → OptiGuide → Optimizer → EvidenceGraph."""
from __future__ import annotations

import copy
import importlib.util
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from kernel.datamodel import (
    KernelResult,
    PlanningContext,
    PolicySnapshot,
    SKUContext,
    SupplierOption,
    scenario_set_to_dict,
    solution_to_dict,
)
from kernel.domain import DomainAdapter
from kernel.multitenant.scheduler import CostEstimate, TenantScheduler
from kernel.forecast.service import ForecastService
from kernel.optiguide.service import OptiGuideService
from kernel.optimizer.service import OptimizerService
from kernel.simulation.service import SimulationService
from kernel.policy.service import PolicyGuardService
from kernel.llm import LLMClient

# Dynamically import evidence-graph/service.py to avoid circular imports
evidence_graph_path = os.path.join(os.path.dirname(__file__), "evidence-graph", "service.py")
spec = importlib.util.spec_from_file_location("evidence_graph_service", evidence_graph_path)
evidence_graph_module = importlib.util.module_from_spec(spec)
sys.modules["evidence_graph_service"] = evidence_graph_module
spec.loader.exec_module(evidence_graph_module)
EvidenceGraphService = evidence_graph_module.EvidenceGraphService


@dataclass
class TenantContext:
    tenant_id: str
    tier: str


class KernelPipeline:
    """Coordinates kernel modules and collects metadata for a single planning run."""

    def __init__(
        self,
        forecast: ForecastService | None = None,
        optiguide: OptiGuideService | None = None,
        optimizer: OptimizerService | None = None,
        evidence: EvidenceGraphService | None = None,
        simulation: SimulationService | None = None,
        policy_guard: PolicyGuardService | None = None,
        domain_adapter: DomainAdapter | None = None,
        scheduler: TenantScheduler | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.forecast = forecast or ForecastService()
        resolved_policy_guard = policy_guard
        if optiguide is not None:
            resolved_policy_guard = policy_guard or getattr(optiguide, "policy_guard", None)
        self.optiguide = optiguide or OptiGuideService(policy_guard=resolved_policy_guard)
        self.policy_guard = resolved_policy_guard or getattr(self.optiguide, "policy_guard", PolicyGuardService())
        if policy_guard is not None and getattr(self.optiguide, "policy_guard", None) is not policy_guard:
            self.optiguide.policy_guard = policy_guard
            self.policy_guard = policy_guard
        if getattr(self.optiguide, "policy_guard", None) is not self.policy_guard:
            self.optiguide.policy_guard = self.policy_guard
        self.optimizer = optimizer or OptimizerService()
        self.simulation = simulation or SimulationService()
        self.evidence = evidence or EvidenceGraphService()
        self.domain_adapter = domain_adapter
        self.scheduler = scheduler
        self.llm = llm_client or LLMClient()

    def run(
        self,
        goaldsl: Any,
        context: PlanningContext,
        *,
        seed: int | None = None,
        run_id: str | None = None,
        warm_start: Any = None,
        tenant: TenantContext | None = None,
    ) -> Dict[str, Any]:
        adapted_goal = self._apply_goal_adapter(goaldsl)
        adapted_context = self._apply_context_adapter(context)

        scenario_set = self.forecast.generate(adapted_context, seed=seed)
        plan_dna = self._fingerprint_plan_inputs(adapted_goal, adapted_context)
        lease = None
        cost_estimate = self._estimate_cost(adapted_context, scenario_set)
        policy_snapshot = None
        try:
            if self.scheduler and tenant:
                lease = self.scheduler.acquire(tenant.tenant_id, tenant.tier, cost_estimate)
            optiguide_result = self.optiguide.compile(
                adapted_goal,
                adapted_context,
                scenario_set,
                tenant=tenant,
            )
            policy_snapshot = optiguide_result.get("policy_snapshot")
            optimizer_result = self.optimizer.solve(
                optiguide_result["optimodel"],
                optiguide_result["compiled_inputs"],
                adapted_context,
                scenario_set,
                warm_start=warm_start,
            )
            optimodel_sha = self._fingerprint_optimodel(optiguide_result["optimodel"])
        finally:
            if lease is not None:
                actual_cost = self._actual_cost(
                    locals().get("optimizer_result"),
                    adapted_context,
                    scenario_set,
                )
                lease.complete(actual_cost)

        robust_eval = self._robust_evaluate(
            optimizer_result["solution"],
            optiguide_result["compiled_inputs"],
            adapted_context,
            scenario_set,
        )
        optimizer_result["diagnostics"]["robust_eval"] = robust_eval

        simulation_summary = self.simulation.simulate(
            adapted_context,
            optimizer_result["solution"],
            scenario_set,
            compiled_inputs=optiguide_result.get("compiled_inputs", {}),
            seed=seed,
        )
        optimizer_result["diagnostics"]["simulation"] = simulation_summary

        if policy_snapshot is None:
            policy_snapshot = PolicySnapshot(
                allow=True,
                policy_id="policy.guard.v1",
                reasons=[],
                warnings=[],
                controls={},
            )
        policy_snapshot = self.policy_guard.evaluate_solution(
            policy_snapshot,
            optimizer_result["solution"],
            optimizer_result.get("diagnostics", {}),
        )

        evidence_ref = self.evidence.persist(
            optimodel=optiguide_result["optimodel"],
            solution=optimizer_result["solution"],
            scenarios=scenario_set,
            hints=optiguide_result["hints"],
            metadata={
                **optiguide_result.get("metadata", {}),
                "diagnostics": optimizer_result["diagnostics"],
                "seed": seed,
                "run_id": run_id,
                "compiled_inputs": optiguide_result.get("compiled_inputs", {}),
                "optimodel_sha": optimodel_sha,
                "plan_dna": plan_dna,
                "robust_eval": robust_eval,
                "simulation": simulation_summary,
                "policy_snapshot": asdict(policy_snapshot),
            },
        )

        llm_summary = self.llm.summarize_plan(
            context={
                "skus": [sku_ctx.sku for sku_ctx in adapted_context.skus],
                "periods": list(adapted_context.periods),
                "locations": list(adapted_context.locations),
            },
            solution=solution_to_dict(optimizer_result["solution"]),
            diagnostics=optimizer_result["diagnostics"],
            policy=asdict(policy_snapshot),
        )
        optimizer_result["diagnostics"]["llm_summary"] = llm_summary

        kernel_result = KernelResult(
            solution=optimizer_result["solution"],
            evidence=evidence_ref,
            policy=policy_snapshot,
            llm_summary=llm_summary,
        )

        result_payload = {
            "evidence_ref": kernel_result.evidence.uri,
            "forecast": scenario_set_to_dict(scenario_set),
            "optimodel": optiguide_result["optimodel"],
            "optimodel_ir": optiguide_result["optimodel"],
            "solution": solution_to_dict(kernel_result.solution),
            "diagnostics": optimizer_result["diagnostics"],
            "run_id": run_id,
            "seed": seed,
            "optimodel_sha": optimodel_sha,
            "plan_dna": plan_dna,
            "robust_eval": robust_eval,
            "simulation": simulation_summary,
            "policy": asdict(policy_snapshot),
            "llm_summary": llm_summary,
        }
        if self.domain_adapter:
            result_payload = self.domain_adapter.postprocess_solution(result_payload)
        return result_payload

    def delta_solve(
        self,
        goaldsl: Any,
        context: PlanningContext,
        modifications: Dict[str, Any],
        *,
        seed: int | None = None,
        run_id: str | None = None,
        tenant: TenantContext | None = None,
    ) -> Dict[str, Any]:
        base_id = f"{run_id}-baseline" if run_id else None
        baseline = self.run(goaldsl, context, seed=seed, run_id=base_id, tenant=tenant)

        modified_goal = self._apply_goal_modifications(
            goaldsl,
            modifications.get("constraints"),
            modifications.get("policies"),
        )
        modified_context = self._apply_context_modifications(context, modifications.get("context"))
        delta_id = f"{run_id}-delta" if run_id else None
        modified = self.run(
            modified_goal,
            modified_context,
            seed=seed,
            run_id=delta_id,
            warm_start=baseline["solution"]["steps"],
            tenant=tenant,
        )

        baseline_kpis = baseline["solution"]["kpis"]
        modified_kpis = modified["solution"]["kpis"]
        kpi_deltas = {
            key: round(modified_kpis.get(key, 0.0) - baseline_kpis.get(key, 0.0), 4)
            for key in set(baseline_kpis) | set(modified_kpis)
        }

        return {
            "baseline": baseline,
            "modified": modified,
            "kpi_deltas": kpi_deltas,
        }

    def supplier_counterfactual(
        self,
        goaldsl: Any,
        context: PlanningContext,
        *,
        sku: str,
        block_supplier: str,
        seed: int | None = None,
        run_id: str | None = None,
        tenant: TenantContext | None = None,
    ) -> Dict[str, Any]:
        delta = self.delta_solve(
            goaldsl,
            context,
            modifications={"context": {"remove_suppliers": {sku: [block_supplier]}}},
            seed=seed,
            run_id=run_id,
            tenant=tenant,
        )
        return delta

    def _apply_goal_modifications(
        self,
        goaldsl: Any,
        constraint_overrides: Dict[str, Any] | None,
        policy_overrides: Dict[str, Any] | None,
    ) -> Any:
        if isinstance(goaldsl, str):
            return goaldsl
        goal_copy = copy.deepcopy(goaldsl)
        if constraint_overrides:
            goal_copy.setdefault("constraints", {}).update(constraint_overrides)
        if policy_overrides:
            goal_copy.setdefault("policies", {}).update(policy_overrides)
        return goal_copy

    def _apply_context_modifications(
        self,
        context: PlanningContext,
        context_mods: Dict[str, Any] | None,
    ) -> PlanningContext:
        if not context_mods:
            return context
        return self._modified_context_clone(context, context_mods)

    def _modified_context_clone(
        self,
        context: PlanningContext,
        context_mods: Dict[str, Any],
    ) -> PlanningContext:
        remove_suppliers: Dict[str, List[str]] = context_mods.get("remove_suppliers", {})
        moq_overrides: Dict[str, Dict[str, float]] = context_mods.get("moq", {})

        cloned_skus = []
        for sku_ctx in context.skus:
            suppliers = []
            removal_set = set(remove_suppliers.get(sku_ctx.sku, []))
            for supplier in sku_ctx.supplier_options:
                if supplier.supplier_id in removal_set:
                    continue
                override = moq_overrides.get(sku_ctx.sku, {}).get(supplier.supplier_id)
                suppliers.append(
                    SupplierOption(
                        supplier_id=supplier.supplier_id,
                        price=supplier.price,
                        moq=int(override) if override is not None else supplier.moq,
                        lead_time_days=supplier.lead_time_days,
                        co2_per_unit=supplier.co2_per_unit,
                        capacity=supplier.capacity,
                    )
                )
            cloned_skus.append(
                SKUContext(
                    sku=sku_ctx.sku,
                    demand_baseline=dict(sku_ctx.demand_baseline),
                    supplier_options=suppliers,
                )
            )

        return PlanningContext(
            horizon=context.horizon,
            periods=context.periods,
            locations=context.locations,
            skus=cloned_skus,
        )

    def _apply_goal_adapter(self, goaldsl: Any) -> Any:
        if self.domain_adapter:
            return self.domain_adapter.prepare_goal(goaldsl)
        return goaldsl

    def _apply_context_adapter(self, context: PlanningContext) -> PlanningContext:
        if self.domain_adapter:
            return self.domain_adapter.prepare_context(context)
        return context

    def _fingerprint_plan_inputs(
        self,
        goaldsl: Any,
        context: PlanningContext,
    ) -> str:
        goal_payload = goaldsl if not isinstance(goaldsl, str) else {"goal": goaldsl}
        context_payload = {
            "horizon": context.horizon,
            "periods": list(context.periods),
            "locations": list(context.locations),
            "skus": [
                {
                    "sku": sku_ctx.sku,
                    "demand_baseline": sku_ctx.demand_baseline,
                    "supplier_options": [
                        {
                            "supplier_id": opt.supplier_id,
                            "price": opt.price,
                            "moq": opt.moq,
                            "lead_time_days": opt.lead_time_days,
                            "co2_per_unit": opt.co2_per_unit,
                            "capacity": opt.capacity,
                        }
                        for opt in sku_ctx.supplier_options
                    ],
                }
                for sku_ctx in context.skus
            ],
        }
        payload = json.dumps({"goal": goal_payload, "context": context_payload}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _fingerprint_optimodel(self, optimodel: Any) -> str:
        from kernel.datamodel import optimodel_to_dict

        payload = json.dumps(optimodel_to_dict(optimodel), sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _estimate_cost(
        self,
        context: PlanningContext,
        scenario_set,
    ) -> CostEstimate:
        scenario_factor = scenario_set.num_scenarios or len(scenario_set.scenarios)
        solver_sec = scenario_factor * max(len(context.skus), 1) * 0.02
        gpu_sec = 0.0
        llm_tokens = max(len(context.skus), 1) * 100.0
        return CostEstimate(solver_sec=solver_sec, gpu_sec=gpu_sec, llm_tokens=llm_tokens)

    def _actual_cost(
        self,
        optimizer_result: Any,
        context: PlanningContext,
        scenario_set,
    ) -> CostEstimate:
        if not optimizer_result:
            return CostEstimate()
        get = getattr
        diagnostics = (
            optimizer_result.get("diagnostics", {})
            if isinstance(optimizer_result, dict)
            else getattr(optimizer_result, "diagnostics", {})
        )
        reduced = diagnostics.get("reduction", {}).get("reduced_count", scenario_set.num_scenarios)
        solver_sec = reduced * max(len(context.skus), 1) * 0.02
        gpu_sec = 0.0
        solution_obj = (
            optimizer_result.get("solution")
            if isinstance(optimizer_result, dict)
            else getattr(optimizer_result, "solution", None)
        )
        if solution_obj is None:
            step_count = 0
        elif isinstance(solution_obj, dict):
            step_count = len(solution_obj.get("steps", []))
        else:
            step_count = len(get(solution_obj, "steps", []))
        llm_tokens = max(step_count, 1) * 50.0
        return CostEstimate(solver_sec=solver_sec, gpu_sec=gpu_sec, llm_tokens=llm_tokens)

    def _robust_evaluate(
        self,
        solution: Dict[str, Any],
        compiled_inputs: Dict[str, Any],
        context: PlanningContext,
        scenario_set,
    ) -> Dict[str, Any]:
        solution_payload = solution
        if not isinstance(solution, dict):
            try:
                solution_payload = solution_to_dict(solution)  # handles dataclass inputs
            except Exception:  # pragma: no cover - defensive fallback
                solution_payload = {
                    "steps": getattr(solution, "steps", []),
                    "kpis": getattr(solution, "kpis", {}),
                }

        stress = self.forecast.stress_sample(context, samples=20)
        supply: Dict[str, Dict[str, float]] = {}
        base_cost = 0.0
        for step in solution_payload.get("steps", []):
            sku = step["sku"]
            period = step["period"]
            supply.setdefault(sku, {})
            supply[sku][period] = supply[sku].get(period, 0.0) + step["quantity"]
            base_cost += step["quantity"] * step.get("price", 0.0)

        prices: Dict[str, Dict[str, float]] = compiled_inputs.get("prices", {})
        scenario_costs: List[float] = []
        scenario_service: List[float] = []

        for scenario in stress.scenarios:
            fulfilled = 0.0
            required = 0.0
            shortage_cost = 0.0
            for sku, demand_map in scenario.demand.items():
                sku_prices = prices.get(sku, {})
                max_price = max(sku_prices.values(), default=1.0)
                for period, demand in demand_map.items():
                    available = supply.get(sku, {}).get(period, 0.0)
                    fulfilled += min(available, demand)
                    required += demand
                    shortage = max(demand - available, 0.0)
                    shortage_cost += shortage * max_price * 1.5
            service_level = fulfilled / required if required else 1.0
            scenario_service.append(service_level)
            scenario_costs.append(base_cost + shortage_cost)

        if scenario_costs:
            sorted_costs = sorted(scenario_costs)
            tail = sorted_costs[int(len(sorted_costs) * 0.9):] or sorted_costs[-1:]
            cvar_cost = sum(tail) / len(tail)
        else:
            cvar_cost = base_cost
        worst_service = min(scenario_service) if scenario_service else 1.0

        return {
            "stress_samples": len(stress.scenarios),
            "worst_case_service": round(worst_service, 4),
            "cvar_cost": round(cvar_cost, 2),
        }



if __name__ == "__main__":
    from kernel.datamodel import SKUContext, SupplierOption

    context = PlanningContext(
        horizon=2,
        periods=["2025-09-01", "2025-09-02"],
        locations=["default"],
        skus=[
            SKUContext(
                sku="SKU1",
                demand_baseline={"2025-09-01": 100, "2025-09-02": 120},
                supplier_options=[
                    SupplierOption(supplier_id="SUP1", price=10.0, moq=10, lead_time_days=2, co2_per_unit=0.5),
                    SupplierOption(supplier_id="SUP2", price=11.0, moq=5, lead_time_days=3, co2_per_unit=0.6),
                ],
            ),
            SKUContext(
                sku="SKU2",
                demand_baseline={"2025-09-01": 80, "2025-09-02": 90},
                supplier_options=[
                    SupplierOption(supplier_id="SUP3", price=9.5, moq=1, lead_time_days=1, co2_per_unit=0.4),
                ],
            ),
        ],
    )
    goaldsl = {
        "objective": {"cost": 0.7, "service": 0.2, "co2": 0.1},
        "constraints": {"budget_month": 8000, "service_min": 0.95},
        "policies": {"vendor_blocklist": []},
    }

    pipeline = KernelPipeline()
    result = pipeline.run(goaldsl, context, seed=4242, run_id="example-run")
    print("Evidence Ref:", result["evidence_ref"])
    print("Forecast Stats:", result["forecast"]["stats"])  # type: ignore[index]
    print("Solution Steps:", result["solution"]["steps"])  # type: ignore[index]
    print("Diagnostics:", result["diagnostics"])
