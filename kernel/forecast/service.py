"""Forecast service implementing scenario generation with caching and summaries."""
from __future__ import annotations

import hashlib
import json
import logging
import math
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List, Sequence

from kernel.datamodel import (
    PlanningContext,
    Scenario,
    ScenarioSet,
    scenario_set_from_dict,
    scenario_set_to_dict,
)


@dataclass
class ForecastConfig:
    """Configuration for scenario generation and caching."""

    num_scenarios: int = 50
    horizon: int = 4
    demand_variation: float = 0.2
    lead_time_variation: int = 1
    clip_negative: bool = True
    cache_dir: Path | None = None
    random_seed: int = 42
    minimum_history_points: int = 3
    fallback_sigma_multiplier: float = 1.5


class ForecastCache:
    """Simple file-backed cache for deterministic scenario generation."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, key: str) -> ScenarioSet | None:
        cache_path = self.cache_dir / f"{key}.json"
        if not cache_path.exists():
            return None
        with cache_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return scenario_set_from_dict(payload)

    def store(self, key: str, scenario_set: ScenarioSet) -> None:
        cache_path = self.cache_dir / f"{key}.json"
        with cache_path.open("w", encoding="utf-8") as handle:
            json.dump(scenario_set_to_dict(scenario_set), handle, indent=2)


class ForecastService:
    """Generates Monte Carlo demand/lead-time scenarios with caching and stats."""

    def __init__(self, config: ForecastConfig | None = None) -> None:
        self.config = config or ForecastConfig()
        self._rng = random.Random(self.config.random_seed)
        cache_directory = self.config.cache_dir or Path(__file__).resolve().parent / ".cache"
        self._cache = ForecastCache(cache_directory)
        self.metrics: Dict[str, float] = {"cache_hits": 0.0, "cache_misses": 0.0}
        self.last_run_info: Dict[str, object] = {}
        self.feedback_history: Dict[str, List[float]] = {}
        self._logger = logging.getLogger(__name__)

    def generate(self, context: PlanningContext, seed: int | None = None) -> ScenarioSet:
        """Generate scenarios for the provided planning context."""

        if seed is not None:
            self._rng.seed(seed)

        cache_key = self._signature(context)
        cached = self._cache.load(cache_key)
        if cached is not None:
            self.metrics["cache_hits"] += 1
            self.last_run_info = {
                "cached": True,
                "fallback_skus": [],
                "scenario_count": cached.num_scenarios,
            }
            return cached
        self.metrics["cache_misses"] += 1

        periods = list(context.periods)
        skus = [sku_ctx.sku for sku_ctx in context.skus]
        scenarios: List[Scenario] = []
        fallback_skus: List[str] = []

        residual_bank = {
            sku_ctx.sku: self._build_residuals(sku_ctx.demand_baseline.values())
            for sku_ctx in context.skus
        }

        for scenario_id in range(self.config.num_scenarios):
            demand: Dict[str, Dict[str, float]] = {}
            lead_times: Dict[str, int] = {}

            for sku_ctx in context.skus:
                sku_demand: Dict[str, float] = {}
                history = sku_ctx.demand_baseline
                base_series = [history.get(period, 0.0) for period in periods]
                fallback_mode = self._requires_fallback(base_series)
                if fallback_mode:
                    fallback_skus.append(sku_ctx.sku)

                for idx, period in enumerate(periods):
                    baseline = base_series[idx]
                    residual = self._sample_residual(residual_bank[sku_ctx.sku])
                    variation_scale = self.config.demand_variation
                    if fallback_mode:
                        variation_scale *= self.config.fallback_sigma_multiplier
                    variation = self._rng.gauss(0, variation_scale)
                    value = baseline + residual + baseline * variation
                    if self.config.clip_negative:
                        value = max(value, 0.0)
                    sku_demand[period] = round(value, 3)
                demand[sku_ctx.sku] = sku_demand

                lead_times[sku_ctx.sku] = self._sample_lead_time(sku_ctx)

            scenarios.append(
                Scenario(
                    id=scenario_id,
                    demand=demand,
                    lead_time_days=lead_times,
                )
            )

        stats = self._summarize(scenarios, skus, periods)
        backtest = self._backtest(context)
        feedback_summary = self._apply_feedback(context)
        scenario_set = ScenarioSet(
            horizon=self.config.horizon,
            num_scenarios=len(scenarios),
            skus=skus,
            scenarios=scenarios,
            stats=stats,
        )
        self._cache.store(cache_key, scenario_set)
        self.last_run_info = {
            "cached": False,
            "fallback_skus": fallback_skus,
            "scenario_count": len(scenarios),
            "backtest": backtest,
            "feedback": feedback_summary,
        }
        if fallback_skus:
            self._logger.info(
                "Forecast fallback activated for SKUs: %s",
                ",".join(sorted(fallback_skus)),
            )
        return scenario_set

    def _signature(self, context: PlanningContext) -> str:
        fingerprint_payload = json.dumps(
            {
                "horizon": context.horizon,
                "periods": list(context.periods),
                "skus": [
                    {
                        "sku": sku_ctx.sku,
                        "baseline": sku_ctx.demand_baseline,
                        "suppliers": [
                            {
                                "supplier_id": supplier.supplier_id,
                                "price": supplier.price,
                                "moq": supplier.moq,
                                "lead_time_days": supplier.lead_time_days,
                                "co2_per_unit": supplier.co2_per_unit,
                                "capacity": supplier.capacity,
                            }
                            for supplier in sku_ctx.supplier_options
                        ],
                    }
                    for sku_ctx in context.skus
                ],
            },
            sort_keys=True,
        )
        hash_key = hashlib.sha256(fingerprint_payload.encode("utf-8")).hexdigest()
        return hash_key

    def _build_residuals(self, series: Iterable[float]) -> List[float]:
        observations = list(series)
        if len(observations) < 3:
            return [0.0]
        rolling_avg = mean(observations)
        residuals = [value - rolling_avg for value in observations]
        if all(abs(residual) < 1e-6 for residual in residuals):
            return [0.0]
        return residuals

    def _requires_fallback(self, base_series: Sequence[float]) -> bool:
        non_zero = [value for value in base_series if value > 0]
        return len(non_zero) < self.config.minimum_history_points

    def _sample_residual(self, residuals: Sequence[float]) -> float:
        if not residuals:
            return 0.0
        return self._rng.choice(residuals)

    def _sample_lead_time(self, sku_ctx) -> int:
        supplier_options = sku_ctx.supplier_options
        if not supplier_options:
            return 0
        base = mean(option.lead_time_days for option in supplier_options)
        jitter = self._rng.randint(-self.config.lead_time_variation, self.config.lead_time_variation)
        return max(int(round(base + jitter)), 0)

    def _summarize(
        self, scenarios: Sequence[Scenario], skus: Sequence[str], periods: Sequence[str]
    ) -> Dict[str, Dict[str, float]]:
        summary: Dict[str, Dict[str, float]] = {}
        for sku in skus:
            samples: List[float] = []
            per_period_quantiles: Dict[str, float] = {}
            for scenario in scenarios:
                samples.extend(scenario.demand[sku][period] for period in periods)
            if not samples:
                continue
            summary[sku] = {
                "mean": round(mean(samples), 4),
                "sigma": round(pstdev(samples), 4),
                "p95": round(self._percentile(samples, 0.95), 4),
                "p10": round(self._percentile(samples, 0.10), 4),
                "conformal_lower": round(self._conformal_interval(samples)[0], 4),
                "conformal_upper": round(self._conformal_interval(samples)[1], 4),
            }
            for period in periods:
                observations = [scenario.demand[sku][period] for scenario in scenarios]
                per_period_quantiles[f"{period}_p95"] = round(self._percentile(observations, 0.95), 4)
            summary[sku].update(per_period_quantiles)
        return summary

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

    def _conformal_interval(self, samples: Sequence[float]) -> tuple[float, float]:
        if not samples:
            return (0.0, 0.0)
        mean_value = mean(samples)
        sigma = pstdev(samples) if len(samples) > 1 else 0.0
        # Simple proxy: mean ± 1.96 * sigma
        return (mean_value - 1.96 * sigma, mean_value + 1.96 * sigma)

    def _backtest(self, context: PlanningContext) -> Dict[str, float]:
        results: Dict[str, float] = {}
        for sku_ctx in context.skus:
            history = sku_ctx.demand_baseline
            if len(history) < 2:
                continue
            periods = sorted(history.keys())
            mid = max(len(periods) // 2, 1)
            train = [history[p] for p in periods[:mid]]
            test = [history[p] for p in periods[mid:]]
            if not train or not test:
                continue
            train_mean = mean(train)
            absolute_errors = [abs(train_mean - actual) for actual in test]
            denom = sum(abs(actual) for actual in test) or 1.0
            mape = sum(absolute_errors) / denom
            results[sku_ctx.sku] = round(mape, 4)
        return results

    def ingest_feedback(self, sku: str, actuals: Dict[str, float]) -> None:
        history = self.feedback_history.setdefault(sku, [])
        history.extend(actuals.values())

    def _apply_feedback(self, context: PlanningContext) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        for sku_ctx in context.skus:
            history = self.feedback_history.get(sku_ctx.sku)
            if not history:
                continue
            avg_actual = sum(history) / len(history)
            summary[sku_ctx.sku] = {
                "observations": len(history),
                "avg_actual": round(avg_actual, 3),
            }
        return summary

    def stress_sample(
        self,
        context: PlanningContext,
        *,
        samples: int = 20,
        tail_factor: float = 1.6,
        seed: int | None = None,
    ) -> ScenarioSet:
        rng = random.Random(seed or (self.config.random_seed + 99))
        periods = list(context.periods)
        skus = [sku_ctx.sku for sku_ctx in context.skus]
        scenarios: List[Scenario] = []

        for scenario_id in range(samples):
            demand: Dict[str, Dict[str, float]] = {}
            lead_times: Dict[str, int] = {}
            for sku_ctx in context.skus:
                sku_demand: Dict[str, float] = {}
                for period in periods:
                    base = sku_ctx.demand_baseline.get(period, 0.0)
                    shock = abs(rng.gauss(0, self.config.demand_variation * tail_factor))
                    value = max(base * (1.0 + shock), 0.0)
                    sku_demand[period] = round(value, 3)
                demand[sku_ctx.sku] = sku_demand

                base_lead = min(
                    (opt.lead_time_days for opt in sku_ctx.supplier_options),
                    default=2,
                )
                lead_times[sku_ctx.sku] = max(int(round(base_lead + rng.uniform(0, tail_factor))), 0)

            scenarios.append(Scenario(id=scenario_id, demand=demand, lead_time_days=lead_times))

        return ScenarioSet(
            horizon=self.config.horizon,
            num_scenarios=len(scenarios),
            skus=skus,
            scenarios=scenarios,
            stats={},
        )
