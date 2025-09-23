"""Synthetic forecast generator following the Kernel design contract."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List

from kernel.datamodel import PlanningContext, Scenario, ScenarioSet


@dataclass
class ForecastConfig:
    num_scenarios: int = 50
    horizon: int = 4
    demand_variation: float = 0.15
    lead_time_variation: int = 1
    random_seed: int = 42


class ForecastService:
    """Generates Monte Carlo demand/lead-time scenarios from baseline context."""

    def __init__(self, config: ForecastConfig | None = None) -> None:
        self.config = config or ForecastConfig()
        self._rng = random.Random(self.config.random_seed)

    def generate(self, context: PlanningContext) -> ScenarioSet:
        periods = list(context.periods)
        skus = [sku_ctx.sku for sku_ctx in context.skus]
        scenarios: List[Scenario] = []

        for scenario_id in range(self.config.num_scenarios):
            demand: Dict[str, Dict[str, float]] = {}
            lead_times: Dict[str, int] = {}

            for sku_ctx in context.skus:
                sku_demand: Dict[str, float] = {}
                for period in periods:
                    base = sku_ctx.demand_baseline.get(period, 0.0)
                    variation = self._rng.gauss(0, self.config.demand_variation)
                    value = max(base * (1.0 + variation), 0.0)
                    sku_demand[period] = round(value, 2)
                demand[sku_ctx.sku] = sku_demand

                avg_lead = sum(opt.lead_time_days for opt in sku_ctx.supplier_options) / max(
                    len(sku_ctx.supplier_options), 1
                )
                jitter = self._rng.randint(-self.config.lead_time_variation, self.config.lead_time_variation)
                lead_times[sku_ctx.sku] = max(int(round(avg_lead + jitter)), 0)

            scenarios.append(Scenario(id=scenario_id, demand=demand, lead_time_days=lead_times))

        stats = self._summarize(scenarios, skus, periods)
        return ScenarioSet(
            horizon=self.config.horizon,
            num_scenarios=len(scenarios),
            skus=skus,
            scenarios=scenarios,
            stats=stats,
        )

    def _summarize(
        self, scenarios: List[Scenario], skus: List[str], periods: List[str]
    ) -> Dict[str, Dict[str, float]]:
        summary: Dict[str, Dict[str, float]] = {}
        for sku in skus:
            observations: List[float] = []
            for scenario in scenarios:
                observations.extend(scenario.demand[sku][p] for p in periods)
            if not observations:
                continue
            mean = sum(observations) / len(observations)
            variance = sum((x - mean) ** 2 for x in observations) / len(observations)
            sigma = math.sqrt(variance)
            p95 = self._percentile(observations, 0.95)
            summary[sku] = {
                "mean": round(mean, 3),
                "sigma": round(sigma, 3),
                "p95": round(p95, 3),
            }
        return summary

    @staticmethod
    def _percentile(samples: List[float], quantile: float) -> float:
        if not samples:
            return 0.0
        ordered = sorted(samples)
        rank = (len(ordered) - 1) * quantile
        lower = int(math.floor(rank))
        upper = int(math.ceil(rank))
        if lower == upper:
            return ordered[lower]
        weight = rank - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight
