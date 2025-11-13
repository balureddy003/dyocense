"""
Adaptive Health Engine (P0 scaffold)

Provides uncertainty-aware health scoring and data quality assessment.
Behind feature flag: ENABLE_ADAPTIVE_HEALTH=true
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
from math import sqrt
from datetime import datetime

from .health_score import HealthScoreResponse, HealthScoreBreakdown, HealthScoreCalculator


@dataclass
class ComponentState:
    mean: float
    variance: float
    count: int


class SimpleBayesUpdater:
    """Minimal Bayesian updater for scalar signals with known observation variance.
    This is a placeholder; in P1 we can persist priors per tenant/component.
    """
    def __init__(self, prior_mean: float = 60.0, prior_var: float = 200.0, obs_var: float = 150.0):
        self.prior_mean = prior_mean
        self.prior_var = prior_var
        self.obs_var = obs_var

    def update(self, observed: float) -> Tuple[float, float]:
        k = self.prior_var / (self.prior_var + self.obs_var)
        post_mean = self.prior_mean + k * (observed - self.prior_mean)
        post_var = (1 - k) * self.prior_var
        return post_mean, post_var


def _estimate_quality(connector_data: Dict[str, Any]) -> float:
    """Compute a lightweight data quality index (0-1).
    Factors: freshness (orders in last 7d), completeness (presence of orders/inventory/customers),
    and basic anomaly proxy (zero/negative amounts).
    """
    orders = connector_data.get("orders", []) or []
    inventory = connector_data.get("inventory", []) or []
    customers = connector_data.get("customers", []) or []

    # Completeness
    has_orders = 1.0 if orders else 0.0
    has_inventory = 1.0 if inventory else 0.0
    has_customers = 1.0 if customers else 0.0
    completeness = (has_orders + has_inventory + has_customers) / 3.0

    # Freshness: any order in last 7 days
    from datetime import datetime, timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    fresh = 0.0
    for o in orders[:200]:
        try:
            ts = o.get("created_at")
            if ts:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00')) if 'T' in ts else datetime.strptime(ts, "%Y-%m-%d")
                if dt >= seven_days_ago:
                    fresh = 1.0
                    break
        except Exception:
            pass

    # Anomaly proxy: fraction of orders with non-positive total
    if orders:
        bad = sum(1 for o in orders if float(o.get("total_amount", 0)) <= 0)
        anomaly = max(0.0, 1.0 - (bad / max(1, len(orders))))
    else:
        anomaly = 0.7  # neutral-ish when no orders

    # Aggregate
    return max(0.0, min(1.0, 0.5 * completeness + 0.3 * fresh + 0.2 * anomaly))


class AdaptiveHealthEngine:
    """Wraps the existing deterministic calculator, adds CI and quality-aware adjustments."""
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        # TODO (P1): load/persist per-tenant priors
        self._bayes = SimpleBayesUpdater()

    def calculate(self, connector_data: Dict[str, Any]) -> HealthScoreResponse:
        # Start from deterministic baseline (re-using existing logic)
        baseline = HealthScoreCalculator(connector_data).calculate_overall_health()

        # Compute quality index and apply a mild attenuation if quality is low
        q = _estimate_quality(connector_data)
        adjusted_score = int(round(baseline.score * (0.85 + 0.15 * q)))  # 0.85..1.0 scaling

        # Simple posterior update of overall score to produce a CI
        mean, var = self._bayes.update(adjusted_score)
        std = sqrt(max(1e-6, var))
        ci_low = max(0.0, mean - 1.96 * std)
        ci_high = min(100.0, mean + 1.96 * std)

        # Return enriched response (keep breakdown/trend/period intact)
        return HealthScoreResponse(
            score=int(round(mean)),
            trend=baseline.trend,
            breakdown=baseline.breakdown,
            last_updated=datetime.now(),
            period_days=baseline.period_days,
            ci_low=round(ci_low, 1),
            ci_high=round(ci_high, 1),
            quality_score=round(q, 3),
        )
