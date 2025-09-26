"""Core datamodel definitions for the Dyocense decision kernel.

These dataclasses implement the contracts described in ``kernel/KernelDESIGN.md``
and the per-module design documents.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple


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
    "scenario_set_to_dict",
    "scenario_set_from_dict",
    "optimodel_to_dict",
    "optimodel_from_dict",
    "solution_to_dict",
    "solution_from_dict",
]


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def scenario_set_to_dict(scenario_set: ScenarioSet) -> Dict[str, Any]:
    """Convert ScenarioSet dataclass into a JSON-serializable dict."""

    data = asdict(scenario_set)
    return data


def scenario_set_from_dict(payload: Dict[str, Any]) -> ScenarioSet:
    """Reconstruct a ScenarioSet dataclass from a dictionary payload."""

    scenarios = [Scenario(**scenario) for scenario in payload.get("scenarios", [])]
    return ScenarioSet(
        horizon=payload["horizon"],
        num_scenarios=payload["num_scenarios"],
        skus=list(payload.get("skus", [])),
        scenarios=scenarios,
        stats=dict(payload.get("stats", {})),
    )


def optimodel_to_dict(model: OptiModel) -> Dict[str, Any]:
    """Convert OptiModel dataclass to a dictionary representation."""

    def _variable(defn: VariableDef) -> Dict[str, Any]:
        data = {
            "name": defn.name,
            "vartype": defn.vartype,
            "lower_bound": defn.lower_bound,
        }
        if defn.upper_bound is not None:
            data["upper_bound"] = defn.upper_bound
        return data

    model_dict = {
        "vars": {name: _variable(defn) for name, defn in model.vars.items()},
        "objective_sense": model.objective_sense,
        "objective_terms": [
            {
                "name": term.name,
                "weight": term.weight,
                "expression": term.expression,
            }
            for term in model.objective_terms
        ],
        "constraints": [
            {
                "name": constraint.name,
                "expression": constraint.expression,
            }
            for constraint in model.constraints
        ],
    }
    if model.robust is not None:
        model_dict["robust"] = {
            "scenarios": model.robust.scenarios,
            "aggregation": model.robust.aggregation,
        }
    return model_dict


def optimodel_from_dict(payload: Dict[str, Any]) -> OptiModel:
    """Reconstruct OptiModel from dictionary representation."""

    vars_dict = {
        name: VariableDef(
            name=value.get("name", name),
            vartype=value["vartype"],
            lower_bound=value.get("lower_bound", 0.0),
            upper_bound=value.get("upper_bound"),
        )
        for name, value in payload.get("vars", {}).items()
    }
    objective_terms = [
        ObjectiveTerm(
            name=item["name"],
            weight=item["weight"],
            expression=item["expression"],
        )
        for item in payload.get("objective_terms", [])
    ]
    constraints = [
        ConstraintDef(name=item["name"], expression=item["expression"])
        for item in payload.get("constraints", [])
    ]
    robust_payload = payload.get("robust")
    robust = None
    if robust_payload:
        robust = RobustConfig(
            scenarios=robust_payload["scenarios"],
            aggregation=robust_payload["aggregation"],
        )
    return OptiModel(
        vars=vars_dict,
        objective_sense=payload.get("objective_sense", "min"),
        objective_terms=objective_terms,
        constraints=constraints,
        robust=robust,
    )


def solution_to_dict(solution: Solution) -> Dict[str, Any]:
    """Convert Solution dataclass to dictionary."""

    data = asdict(solution)
    return data


def solution_from_dict(payload: Dict[str, Any]) -> Solution:
    """Reconstruct Solution dataclass from dictionary payload."""

    steps = [PlanStep(**step) for step in payload.get("steps", [])]
    return Solution(
        status=payload["status"],
        gap=payload.get("gap", 0.0),
        kpis=dict(payload.get("kpis", {})),
        steps=steps,
        binding_constraints=list(payload.get("binding_constraints", [])),
        activities=dict(payload.get("activities", {})),
        shadow_prices=dict(payload.get("shadow_prices", {})),
    )
