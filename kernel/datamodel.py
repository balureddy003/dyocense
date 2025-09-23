"""Core datamodel definitions for the Dyocense decision kernel.

These dataclasses implement the contracts described in ``kernel/KernelDESIGN.md``
and the per-module design documents.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Forecasting
# ---------------------------------------------------------------------------


@dataclass
class SupplierOption:
    """Commercial + operational parameters for a supplier providing a SKU."""

    supplier_id: str
    price: float
    moq: int
    lead_time_days: int
    co2_per_unit: float
    capacity: Optional[float] = None


@dataclass
class SKUContext:
    """Demand and sourcing metadata for a single SKU."""

    sku: str
    demand_baseline: Dict[str, float]
    supplier_options: List[SupplierOption]


@dataclass
class PlanningContext:
    """Normalized planner context used across kernel modules."""

    horizon: int
    periods: Sequence[str]
    locations: Sequence[str]
    skus: List[SKUContext]


@dataclass
class Scenario:
    """Demand / lead time realization for the planning horizon."""

    id: int
    demand: Dict[str, Dict[str, float]]  # sku -> period -> demand quantity
    lead_time_days: Dict[str, int]


@dataclass
class ScenarioSet:
    """Aggregate collection of Monte Carlo scenarios and summary statistics."""

    horizon: int
    num_scenarios: int
    skus: List[str]
    scenarios: List[Scenario]
    stats: Dict[str, Dict[str, float]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# OptiModel IR and explainability hints
# ---------------------------------------------------------------------------


@dataclass
class VariableDef:
    name: str
    vartype: str
    lower_bound: float = 0.0
    upper_bound: Optional[float] = None


@dataclass
class ObjectiveTerm:
    name: str
    weight: float
    expression: str


@dataclass
class ConstraintDef:
    name: str
    expression: str


@dataclass
class RobustConfig:
    scenarios: int
    aggregation: str


@dataclass
class OptiModel:
    vars: Dict[str, VariableDef]
    objective_sense: str
    objective_terms: List[ObjectiveTerm]
    constraints: List[ConstraintDef]
    robust: Optional[RobustConfig] = None


@dataclass
class ExplainabilityHints:
    track: List[str]
    sensitivities: List[str]


# ---------------------------------------------------------------------------
# Optimizer output contracts
# ---------------------------------------------------------------------------


@dataclass
class PlanStep:
    sku: str
    supplier: str
    period: str
    quantity: float
    price: float


@dataclass
class Solution:
    status: str
    gap: float
    kpis: Dict[str, float]
    steps: List[PlanStep]
    binding_constraints: List[str]
    activities: Dict[str, float]
    shadow_prices: Dict[str, float]


# ---------------------------------------------------------------------------
# Evidence graph
# ---------------------------------------------------------------------------


@dataclass
class EvidenceSnapshot:
    plan_id: str
    optimodel: OptiModel
    solution: Solution
    scenarios: ScenarioSet
    hints: ExplainabilityHints


@dataclass
class EvidenceRef:
    uri: str
    snapshot_hash: str


# ---------------------------------------------------------------------------
# Policy guard
# ---------------------------------------------------------------------------


@dataclass
class PolicySnapshot:
    allow: bool
    policy_id: str
    reasons: List[str] = field(default_factory=list)


@dataclass
class PolicyDecision:
    allow: bool
    policy_snapshot: PolicySnapshot


# ---------------------------------------------------------------------------
# Kernel results
# ---------------------------------------------------------------------------


@dataclass
class KernelResult:
    solution: Solution
    evidence: EvidenceRef
    policy: PolicySnapshot


@dataclass
class KernelConfig:
    forecast_num_scenarios: int = 50
    forecast_horizon: int = 4
    optimizer_time_limit_sec: int = 20
    optimizer_mip_gap: float = 0.02
    explainability_track: Tuple[str, ...] = ("budget", "moq", "balance", "lead_time")
    explainability_sensitivities: Tuple[str, ...] = ("price", "moq")


__all__ = [
    "SupplierOption",
    "SKUContext",
    "PlanningContext",
    "Scenario",
    "ScenarioSet",
    "VariableDef",
    "ObjectiveTerm",
    "ConstraintDef",
    "RobustConfig",
    "OptiModel",
    "ExplainabilityHints",
    "PlanStep",
    "Solution",
    "EvidenceSnapshot",
    "EvidenceRef",
    "PolicySnapshot",
    "PolicyDecision",
    "KernelResult",
    "KernelConfig",
]
