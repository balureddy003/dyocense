"""Simulation service for hybrid simulation–optimization analysis."""
from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, Optional

from kernel.datamodel import PlanningContext, ScenarioSet, Solution, solution_to_dict


@dataclass
class SimulationConfig:
    """Configuration controls for hybrid simulation."""

    runs: int = 40
    expedite_penalty_multiplier: float = 1.25
    noise_sigma_scale: float = 0.1
    random_seed: int = 1337


class SimulationService:
    """Runs stochastic simulations of plan execution against scenario demand."""

    def __init__(self, config: SimulationConfig | None = None) -> None:
        self.config = config or SimulationConfig()

    def simulate(
        self,
        context: PlanningContext,
        solution: Solution | Mapping[str, Any],
        scenario_set: ScenarioSet,
        *,
        compiled_inputs: Mapping[str, Any] | None = None,
        runs: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        solution_payload = solution if isinstance(solution, Mapping) else solution_to_dict(solution)
        supply = self._aggregate_supply(solution_payload)
        prices = self._resolve_prices(compiled_inputs, context)

        scenarios = scenario_set.scenarios or []
        if not scenarios:
            return {
                "runs": 0,
                "mean_service": 1.0,
                "p10_service": 1.0,
                "p90_service": 1.0,
                "avg_shortage": 0.0,
                "max_shortage": 0.0,
                "avg_leftover": 0.0,
                "avg_expedite_cost": 0.0,
                "notes": "No scenarios provided for simulation",
            }

        simulations = runs if runs is not None else self.config.runs
        rng = random.Random(seed if seed is not None else self.config.random_seed)
        stats = scenario_set.stats or {}
        services: List[float] = []
        shortages: List[float] = []
        leftovers: List[float] = []
        expedite_costs: List[float] = []

        for _ in range(simulations):
            scenario = rng.choice(scenarios)
            record = self._simulate_single_run(
                context,
                supply,
                scenario.demand,
                stats,
                prices,
                rng,
            )
            services.append(record["service"])
            shortages.append(record["shortage"])
            leftovers.append(record["leftover"])
            expedite_costs.append(record["expedite_cost"])

        services_sorted = sorted(services)
        return {
            "runs": simulations,
            "mean_service": round(mean(services), 4),
            "p10_service": round(self._percentile(services_sorted, 0.10), 4),
            "p90_service": round(self._percentile(services_sorted, 0.90), 4),
            "avg_shortage": round(mean(shortages), 3),
            "max_shortage": round(max(shortages), 3),
            "avg_leftover": round(mean(leftovers), 3),
            "avg_expedite_cost": round(mean(expedite_costs), 2),
        }

    def _simulate_single_run(
        self,
        context: PlanningContext,
        supply: Mapping[str, Mapping[str, float]],
        demand_realization: Mapping[str, Mapping[str, float]],
        stats: Mapping[str, Mapping[str, float]],
        prices: Mapping[str, float],
        rng: random.Random,
    ) -> Dict[str, float]:
        total_demand = 0.0
        fulfilled = 0.0
        total_shortage = 0.0
        leftover = 0.0
        total_expedite_cost = 0.0

        for sku_ctx in context.skus:
            sku = sku_ctx.sku
            sku_supply = supply.get(sku, {})
            sku_demand = demand_realization.get(sku, {})
            sku_stats = stats.get(sku, {})
            sigma = float(sku_stats.get("sigma", 0.0))
            price = prices.get(sku, self._average_supplier_price(sku_ctx.supplier_options))

            for period in context.periods:
                planned = float(sku_supply.get(period, 0.0))
                base_demand = float(sku_demand.get(period, 0.0))
                noise = rng.gauss(0.0, sigma * self.config.noise_sigma_scale)
                realized = max(base_demand + noise, 0.0)
                fulfilled_period = min(planned, realized)
                shortage_period = max(realized - planned, 0.0)
                leftover_period = max(planned - realized, 0.0)
                expedite_cost = shortage_period * price * self.config.expedite_penalty_multiplier

                total_demand += realized
                fulfilled += fulfilled_period
                total_shortage += shortage_period
                leftover += leftover_period
                total_expedite_cost += expedite_cost

        service = fulfilled / total_demand if total_demand else 1.0
        return {
            "service": service,
            "shortage": total_shortage,
            "leftover": leftover,
            "expedite_cost": total_expedite_cost,
        }

    @staticmethod
    def _aggregate_supply(solution_payload: Mapping[str, Any]) -> Dict[str, Dict[str, float]]:
        supply: Dict[str, Dict[str, float]] = {}
        for step in solution_payload.get("steps", []):
            sku = step["sku"]
            period = step["period"]
            quantity = float(step.get("quantity", 0.0))
            supply.setdefault(sku, {})[period] = supply.setdefault(sku, {}).get(period, 0.0) + quantity
        return supply

    @staticmethod
    def _resolve_prices(
        compiled_inputs: Mapping[str, Any] | None,
        context: PlanningContext,
    ) -> Dict[str, float]:
        if not compiled_inputs:
            return {sku_ctx.sku: SimulationService._average_supplier_price(sku_ctx.supplier_options) for sku_ctx in context.skus}
        prices_section = compiled_inputs.get("prices", {})
        prices: Dict[str, float] = {}
        if isinstance(prices_section, Mapping):
            for sku, supplier_prices in prices_section.items():
                if isinstance(supplier_prices, Mapping) and supplier_prices:
                    numeric_prices = [float(price) for price in supplier_prices.values()]
                    prices[sku] = sum(numeric_prices) / len(numeric_prices)
        if not prices:
            return {sku_ctx.sku: SimulationService._average_supplier_price(sku_ctx.supplier_options) for sku_ctx in context.skus}
        return prices

    @staticmethod
    def _average_supplier_price(suppliers: Iterable[Any]) -> float:
        prices = [float(getattr(supplier, "price", 0.0)) for supplier in suppliers if getattr(supplier, "price", None) is not None]
        return sum(prices) / len(prices) if prices else 1.0

    @staticmethod
    def _percentile(sorted_values: List[float], quantile: float) -> float:
        if not sorted_values:
            return 0.0
        index = quantile * (len(sorted_values) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_values) - 1)
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
