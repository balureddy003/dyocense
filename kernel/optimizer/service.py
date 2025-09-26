"""Optimizer module implementing heuristic solver for OptiModel IR."""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from kernel.datamodel import (
    ConstraintDef,
    OptiModel,
    PlanStep,
    PlanningContext,
    ScenarioSet,
    Solution,
)


@dataclass
class OptimizerConfig:
    """Configuration parameters for heuristic optimization."""

    service_quantile: float = 0.95
    slack_penalty: float = 1_000.0
    inventory_penalty: float = 0.05


class OptimizerService:
    """Solves OptiModel IR using deterministic heuristics with diagnostics."""

    def __init__(self, config: OptimizerConfig | None = None) -> None:
        self.config = config or OptimizerConfig()

    def solve(
        self,
        model: OptiModel,
        compiled_inputs: Mapping[str, Any],
        context: PlanningContext,
        scenarios: ScenarioSet,
        warm_start: Any = None,
    ) -> Dict[str, Any]:
        reduction_info = self._scenario_reduction(compiled_inputs, scenarios)
        demand_requirements = self._compute_demand_requirements(
            compiled_inputs,
            context,
            reduction_info["scenario_ids"],
        )
        initial_allocation = (
            self._allocation_from_warm_start(warm_start, context) if warm_start else None
        )
        allocation, shortages = self._allocate_supply(
            compiled_inputs,
            context,
            demand_requirements,
            initial_allocation=initial_allocation,
        )

        lns_iterations = self._lns_iterations(compiled_inputs, reduction_info, context)
        lns_result = None
        blocked = set(compiled_inputs.get("vendor_blocklist", []))
        if lns_iterations > 0:
            allocation, lns_result = self._lns_improve(
                allocation,
                compiled_inputs,
                context,
                demand_requirements,
                iterations=lns_iterations,
                blocked=blocked,
            )

        original_shortages = copy.deepcopy(shortages)
        relaxation_info = None
        if shortages:
            allocation, relaxation_info, shortages = self._auto_relax(
                allocation,
                shortages,
                compiled_inputs,
                context,
                demand_requirements,
            )

        kpis = self._compute_kpis(allocation, compiled_inputs, demand_requirements, shortages)

        status = "FEASIBLE" if not relaxation_info else "FEASIBLE_RELAXED"
        gap = 0.0 if not shortages else 0.05
        binding_constraints = self._binding_constraints(model.constraints, compiled_inputs, kpis, shortages)
        if relaxation_info:
            binding_constraints.append("capacity_relaxed")
        activities = {
            "total_cost": round(kpis["total_cost"], 3),
            "service_level": round(kpis["service_level"], 4),
        }
        shadow_prices: Dict[str, float] = {}

        stress_test = self._stress_test(allocation, compiled_inputs, context)

        solution = Solution(
            status=status,
            gap=gap,
            kpis={
                "total_cost": round(kpis["total_cost"], 3),
                "service_level": round(kpis["service_level"], 4),
                "co2": round(kpis.get("co2", 0.0), 3),
            },
            steps=self._build_plan_steps(allocation, compiled_inputs["prices"]),
            binding_constraints=binding_constraints,
            activities=activities,
            shadow_prices=shadow_prices,
        )

        diagnostics = {
            "status": status,
            "shortages_before_relax": original_shortages,
            "shortages": shortages,
            "service_quantile": self.config.service_quantile,
            "reduction": reduction_info,
            "stress_test": stress_test,
            "warm_start": bool(initial_allocation),
        }
        if shortages:
            diagnostics["status_detail"] = "SHORTAGES"
        if lns_result is not None:
            diagnostics["lns"] = lns_result
        if relaxation_info is not None:
            diagnostics["relaxation"] = relaxation_info

        return {"solution": solution, "diagnostics": diagnostics}

    def _scenario_reduction(
        self,
        compiled_inputs: Mapping[str, Any],
        scenarios: ScenarioSet,
    ) -> Dict[str, Any]:
        constraints = compiled_inputs.get("constraints", {}) or {}
        reduction_cfg = constraints.get("scenario_reduction") or {}
        all_ids = list(compiled_inputs.get("scenario_demand", {}).keys())
        if not all_ids:
            all_ids = [scenario.id for scenario in scenarios.scenarios]
        k = None
        if isinstance(reduction_cfg, Mapping):
            k = reduction_cfg.get("k")
        elif isinstance(reduction_cfg, int):
            k = reduction_cfg
        if not isinstance(k, int) or k <= 0:
            # default reduction when scenario count large
            if len(all_ids) > 20:
                k = min(20, len(all_ids))
            else:
                k = len(all_ids)
        selected = all_ids[:k]
        weights = {scenario_id: round(1.0 / k, 4) for scenario_id in selected}
        return {
            "scenario_ids": selected,
            "original_count": len(all_ids),
            "reduced_count": len(selected),
            "weights": weights,
        }

    def _lns_iterations(
        self,
        compiled_inputs: Mapping[str, Any],
        reduction_info: Mapping[str, Any],
        context: PlanningContext,
    ) -> int:
        constraints = compiled_inputs.get("constraints", {}) or {}
        lns_cfg = constraints.get("lns_iterations")
        iterations: int | None
        if isinstance(lns_cfg, Mapping):
            iterations = lns_cfg.get("iterations")
        elif isinstance(lns_cfg, int):
            iterations = lns_cfg
        else:
            iterations = None
        if iterations is None:
            reduced_count = reduction_info.get("reduced_count", 0)
            hot_set = reduced_count > 15 or len(context.skus) > 2
            iterations = 2 if hot_set else 0
        return max(int(iterations), 0)

    def _compute_demand_requirements(
        self,
        compiled_inputs: Mapping[str, Any],
        context: PlanningContext,
        scenario_ids: Sequence[int],
    ) -> Dict[str, Dict[str, float]]:
        quantile = self.config.service_quantile
        demand_requirements: Dict[str, Dict[str, float]] = {}

        scenario_demand: Mapping[int, Mapping[str, Dict[str, float]]] = compiled_inputs["scenario_demand"]
        for sku_ctx in context.skus:
            sku = sku_ctx.sku
            demand_requirements[sku] = {}
            for period in context.periods:
                samples = [
                    scenario_demand[sid][sku][period]
                    for sid in scenario_ids
                    if sid in scenario_demand
                ]
                demand_requirements[sku][period] = self._percentile(samples, quantile)
        return demand_requirements

    def _allocation_from_warm_start(
        self,
        warm_start: Any,
        context: PlanningContext,
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        allocation: Dict[str, Dict[str, Dict[str, float]]] = {}
        steps = warm_start if isinstance(warm_start, list) else warm_start.get("steps", [])
        for step in steps:
            sku = step["sku"] if isinstance(step, dict) else step.sku
            supplier = step["supplier"] if isinstance(step, dict) else step.supplier
            period = step["period"] if isinstance(step, dict) else step.period
            quantity = step["quantity"] if isinstance(step, dict) else step.quantity
            allocation.setdefault(sku, {})
            allocation[sku].setdefault(supplier, {p: 0.0 for p in context.periods})
            allocation[sku][supplier][period] = allocation[sku][supplier].get(period, 0.0) + float(quantity)
        return allocation

    def _allocate_supply(
        self,
        compiled_inputs: Mapping[str, Any],
        context: PlanningContext,
        demand_requirements: Mapping[str, Mapping[str, float]],
        initial_allocation: Dict[str, Dict[str, Dict[str, float]]] | None = None,
    ) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], Dict[str, Dict[str, float]]]:
        prices: Mapping[str, Mapping[str, float]] = compiled_inputs["prices"]
        capacities: Mapping[str, Mapping[str, float]] = compiled_inputs["capacity"]
        moq: Mapping[str, Mapping[str, float]] = compiled_inputs["moq"]
        blocklist = set(compiled_inputs.get("vendor_blocklist", []))

        allocation: Dict[str, Dict[str, Dict[str, float]]] = {}
        shortages: Dict[str, Dict[str, float]] = {}

        cumulative_supplier_usage: Dict[str, Dict[str, float]] = {}

        for sku_ctx in context.skus:
            sku = sku_ctx.sku
            allocation[sku] = {}
            shortages[sku] = {}
            supplier_order = sorted(
                (
                    (supplier.supplier_id, prices[sku][supplier.supplier_id])
                    for supplier in sku_ctx.supplier_options
                    if supplier.supplier_id not in blocklist
                ),
                key=lambda item: item[1],
            )

            for supplier_id, _ in supplier_order:
                allocation[sku][supplier_id] = {period: 0.0 for period in context.periods}
                cumulative_supplier_usage.setdefault(supplier_id, {})
                cumulative_supplier_usage[supplier_id].setdefault(sku, 0.0)

            if initial_allocation and sku in initial_allocation:
                for supplier_id, period_alloc in initial_allocation[sku].items():
                    allocation.setdefault(sku, {}).setdefault(
                        supplier_id, {period: 0.0 for period in context.periods}
                    )
                    for period, qty in period_alloc.items():
                        allocation[sku][supplier_id][period] = qty
                        cumulative_supplier_usage.setdefault(supplier_id, {})
                        cumulative_supplier_usage[supplier_id][sku] = (
                            cumulative_supplier_usage[supplier_id].get(sku, 0.0) + qty
                        )

            for period in context.periods:
                required = demand_requirements[sku][period]
                initial_supply = sum(
                    allocation[sku][supplier_id].get(period, 0.0) for supplier_id, _ in supplier_order
                )
                remaining = max(required - initial_supply, 0.0)
                for supplier_id, _ in supplier_order:
                    capacity_limit = capacities[sku].get(supplier_id, float("inf"))
                    used_capacity = cumulative_supplier_usage[supplier_id].get(sku, 0.0)
                    available = max(capacity_limit - used_capacity, 0.0)
                    if available <= 0.0:
                        continue
                    order_qty = min(remaining, available)
                    if order_qty <= 0.0:
                        continue
                    allocation[sku][supplier_id][period] += order_qty
                    cumulative_supplier_usage[supplier_id][sku] += order_qty
                    remaining -= order_qty
                    if remaining <= 1e-6:
                        break
                if remaining > 1e-6:
                    shortages[sku][period] = remaining

            # Enforce MOQ post allocation
            for supplier_id, _ in supplier_order:
                total_allocated = sum(allocation[sku][supplier_id].values())
                if 0.0 < total_allocated < moq[sku].get(supplier_id, 0.0):
                    top_up = moq[sku][supplier_id] - total_allocated
                    first_period = context.periods[0]
                    allocation[sku][supplier_id][first_period] += top_up
                    cumulative_supplier_usage[supplier_id][sku] += top_up

            # Clear shortages if MOQs satisfied the deficit
            for period in list(shortages[sku].keys()):
                fulfilled = sum(allocation[sku][supplier_id][period] for supplier_id, _ in supplier_order)
                required = demand_requirements[sku][period]
                if fulfilled >= required:
                    shortages[sku].pop(period, None)
            if not shortages[sku]:
                shortages.pop(sku, None)

        return allocation, shortages

    def _compute_kpis(
        self,
        allocation: Mapping[str, Mapping[str, Mapping[str, float]]],
        compiled_inputs: Mapping[str, Any],
        demand_requirements: Mapping[str, Mapping[str, float]],
        shortages: Mapping[str, Mapping[str, float]],
    ) -> Dict[str, float]:
        prices: Mapping[str, Mapping[str, float]] = compiled_inputs["prices"]
        co2: Mapping[str, Mapping[str, float]] = compiled_inputs["co2"]
        total_cost = 0.0
        total_co2 = 0.0
        fulfilled = 0.0
        required_total = 0.0

        for sku, supplier_allocations in allocation.items():
            sku_prices = prices.get(sku, {})
            sku_co2 = co2.get(sku, {})
            for supplier_id, period_allocations in supplier_allocations.items():
                price = sku_prices.get(supplier_id)
                emission = sku_co2.get(supplier_id)
                if price is None:
                    continue
                for period, qty in period_allocations.items():
                    total_cost += qty * price
                    if emission is not None:
                        total_co2 += qty * emission
                    fulfilled += qty
        for sku, period_demands in demand_requirements.items():
            for qty in period_demands.values():
                required_total += qty
        unfulfilled = sum(sum(period_shortages.values()) for period_shortages in shortages.values())
        fulfilled = max(fulfilled - unfulfilled, 0.0)
        service_level = fulfilled / required_total if required_total else 1.0

        return {
            "total_cost": total_cost,
            "co2": total_co2,
            "service_level": service_level,
        }

    def _binding_constraints(
        self,
        constraints: Sequence[ConstraintDef],
        compiled_inputs: Mapping[str, Any],
        kpis: Mapping[str, float],
        shortages: Mapping[str, Mapping[str, float]],
    ) -> List[str]:
        binding: List[str] = []
        constraint_values = compiled_inputs.get("constraints", {})
        if "budget_month" in constraint_values:
            budget = float(constraint_values["budget_month"])
            if kpis["total_cost"] >= budget * 0.999:
                binding.append("budget_month")
        if shortages:
            binding.append("capacity")
        if "service_min" in constraint_values:
            service_min = float(constraint_values["service_min"])
            if kpis["service_level"] <= service_min:
                binding.append("service_min")
        if not binding:
            binding = [constraints[0].name] if constraints else []
        return binding

    @staticmethod
    def _build_plan_steps(
        allocation: Mapping[str, Mapping[str, Mapping[str, float]]],
        prices: Mapping[str, Mapping[str, float]],
    ) -> List[PlanStep]:
        steps: List[PlanStep] = []
        for sku, supplier_allocations in allocation.items():
            sku_prices = prices.get(sku, {})
            for supplier_id, period_allocations in supplier_allocations.items():
                price = sku_prices.get(supplier_id)
                if price is None:
                    continue
                for period, qty in period_allocations.items():
                    if qty <= 0.0:
                        continue
                    steps.append(
                        PlanStep(
                            sku=sku,
                            supplier=supplier_id,
                            period=str(period),
                            quantity=round(qty, 4),
                            price=price,
                        )
                    )
        return steps

    def _auto_relax(
        self,
        allocation: Dict[str, Dict[str, Dict[str, float]]],
        shortages: Dict[str, Dict[str, float]],
        compiled_inputs: Mapping[str, Any],
        context: PlanningContext,
        demand_requirements: Mapping[str, Mapping[str, float]],
    ) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], Dict[str, Any], Dict[str, Dict[str, float]]]:
        prices: Mapping[str, Mapping[str, float]] = compiled_inputs["prices"]
        capacity: Mapping[str, Mapping[str, float]] = compiled_inputs["capacity"]
        blocked = set(compiled_inputs.get("vendor_blocklist", []))
        relax_adjustments: List[Dict[str, Any]] = []

        for sku, period_shortages in shortages.items():
            sku_prices = {
                supplier: price
                for supplier, price in prices.get(sku, {}).items()
                if supplier not in blocked
            }
            if not sku_prices:
                continue
            cheapest_supplier = min(sku_prices.items(), key=lambda item: item[1])[0]
            allocation.setdefault(sku, {})
            allocation[sku].setdefault(cheapest_supplier, {period: 0.0 for period in context.periods})
            for period, deficit in period_shortages.items():
                if deficit <= 0.0:
                    continue
                allocation[sku][cheapest_supplier][period] += deficit
                relax_adjustments.append(
                    {
                        "constraint": "capacity",
                        "sku": sku,
                        "supplier": cheapest_supplier,
                        "period": period,
                        "additional_qty": round(deficit, 4),
                    }
                )
                capacity.setdefault(sku, {})[cheapest_supplier] = capacity.get(sku, {}).get(
                    cheapest_supplier,
                    0.0,
                ) + deficit

        return allocation, {
            "status": "APPLIED",
            "adjustments": relax_adjustments,
        }, {}

    def _lns_improve(
        self,
        allocation: Dict[str, Dict[str, Dict[str, float]]],
        compiled_inputs: Mapping[str, Any],
        context: PlanningContext,
        demand_requirements: Mapping[str, Mapping[str, float]],
        iterations: int,
        blocked: set[str],
    ) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], Dict[str, Any]]:
        prices: Mapping[str, Mapping[str, float]] = compiled_inputs["prices"]
        capacities: Mapping[str, Mapping[str, float]] = compiled_inputs["capacity"]
        improvement = 0.0
        baseline_cost = self._total_cost(allocation, prices)
        iterations_executed = 0
        for iteration in range(iterations):
            changed = False
            for sku_ctx in context.skus:
                sku = sku_ctx.sku
                supplier_prices = {
                    supplier: price
                    for supplier, price in prices[sku].items()
                    if supplier not in blocked
                }
                sorted_suppliers = sorted(supplier_prices.items(), key=lambda item: item[1])
                if len(sorted_suppliers) < 2:
                    continue
                cheapest, expensive = sorted_suppliers[0], sorted_suppliers[-1]
                cheap_id, cheap_price = cheapest
                exp_id, _ = expensive
                if exp_id not in allocation[sku]:
                    continue
                exp_total = sum(allocation[sku][exp_id].values())
                if exp_total <= 0.0:
                    continue
                transferable = exp_total * 0.2
                # Ensure cheap supplier capacity remains
                current_cheap = sum(allocation[sku].get(cheap_id, {}).values())
                capacity_limit = capacities[sku].get(cheap_id, float("inf"))
                available_capacity = max(capacity_limit - current_cheap, 0.0)
                move_qty = min(transferable, available_capacity)
                if move_qty <= 0.0:
                    continue
                first_period = context.periods[0]
                allocation[sku].setdefault(cheap_id, {period: 0.0 for period in context.periods})
                allocation[sku][exp_id][first_period] = max(
                    allocation[sku][exp_id].get(first_period, 0.0) - move_qty,
                    0.0,
                )
                allocation[sku][cheap_id][first_period] = (
                    allocation[sku][cheap_id].get(first_period, 0.0) + move_qty
                )
                changed = True
            if not changed:
                break
            iterations_executed = iteration + 1
        new_cost = self._total_cost(allocation, prices)
        improvement = baseline_cost - new_cost
        return allocation, {
            "iterations_requested": iterations,
            "cost_improvement": round(improvement, 4),
            "iterations_executed": iterations_executed,
        }

    def _total_cost(
        self,
        allocation: Mapping[str, Mapping[str, Mapping[str, float]]],
        prices: Mapping[str, Mapping[str, float]],
    ) -> float:
        total = 0.0
        for sku, supplier_allocations in allocation.items():
            sku_prices = prices.get(sku, {})
            for supplier_id, period_allocations in supplier_allocations.items():
                price = sku_prices.get(supplier_id)
                if price is None:
                    continue
                for qty in period_allocations.values():
                    total += qty * price
        return total

    def _stress_test(
        self,
        allocation: Mapping[str, Mapping[str, Mapping[str, float]]],
        compiled_inputs: Mapping[str, Any],
        context: PlanningContext,
    ) -> Dict[str, Any]:
        scenario_demand: Mapping[int, Mapping[str, Dict[str, float]]] = compiled_inputs["scenario_demand"]
        min_service = 1.0
        scenario_service: Dict[int, float] = {}
        for scenario_id, sku_demands in scenario_demand.items():
            fulfilled = 0.0
            required = 0.0
            for sku, period_demands in sku_demands.items():
                for period, demand_qty in period_demands.items():
                    supply = sum(
                        allocation.get(sku, {}).get(supplier_id, {}).get(period, 0.0)
                        for supplier_id in allocation.get(sku, {})
                    )
                    fulfilled += min(supply, demand_qty)
                    required += demand_qty
            service_level = fulfilled / required if required else 1.0
            scenario_service[scenario_id] = round(service_level, 4)
            min_service = min(min_service, service_level)
        return {
            "scenario_service": scenario_service,
            "worst_case_service": round(min_service, 4),
        }

    @staticmethod
    def _percentile(samples: Sequence[float], quantile: float) -> float:
        ordered = sorted(samples)
        if not ordered:
            return 0.0
        rank = (len(ordered) - 1) * quantile
        lower = int(math.floor(rank))
        upper = int(math.ceil(rank))
        if lower == upper:
            return ordered[lower]
        weight = rank - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight
