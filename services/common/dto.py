"""Typed data transfer objects shared across Dyocense services."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, MutableMapping, Optional


@dataclass(slots=True)
class Scenario:
    """Single demand/lead-time realization."""

    id: int
    demand: Dict[str, Dict[str, float]]
    lead_time_days: Dict[str, float]

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "Scenario":
        return Scenario(
            id=int(payload.get("id", 0)),
            demand={sku: dict(values) for sku, values in payload.get("demand", {}).items()},
            lead_time_days={sku: float(value) for sku, value in payload.get("lead_time_days", {}).items()},
        )


@dataclass(slots=True)
class ScenarioSet:
    horizon: int
    num_scenarios: int
    skus: List[str]
    scenarios: List[Scenario]
    stats: Dict[str, Dict[str, float]] = field(default_factory=dict)

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "ScenarioSet":
        scenarios = [Scenario.from_dict(item) for item in payload.get("scenarios", [])]
        return ScenarioSet(
            horizon=int(payload.get("horizon", 0)),
            num_scenarios=int(payload.get("num_scenarios", len(scenarios))),
            skus=list(payload.get("skus", [])),
            scenarios=scenarios,
            stats={sku: dict(values) for sku, values in payload.get("stats", {}).items()},
        )


@dataclass(slots=True)
class ExplainabilityHints:
    track: List[str]
    sensitivities: List[str]

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "ExplainabilityHints":
        return ExplainabilityHints(
            track=list(payload.get("track", [])),
            sensitivities=list(payload.get("sensitivities", [])),
        )


@dataclass(slots=True)
class OptiModel:
    vars: Dict[str, Any]
    objective_sense: str
    objective_terms: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    robust: Optional[Dict[str, Any]] = None

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "OptiModel":
        return OptiModel(
            vars=dict(payload.get("vars", {})),
            objective_sense=str(payload.get("objective_sense", payload.get("obj", {}).get("sense", "min"))),
            objective_terms=list(payload.get("objective_terms", payload.get("obj", {}).get("terms", []))),
            constraints=list(payload.get("constraints", [])),
            robust=payload.get("robust"),
        )


@dataclass(slots=True)
class SolutionStep:
    sku: str
    supplier: str
    period: str
    quantity: float
    price: Optional[float] = None

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "SolutionStep":
        return SolutionStep(
            sku=str(payload.get("sku")),
            supplier=str(payload.get("supplier")),
            period=str(payload.get("period")),
            quantity=float(payload.get("quantity", 0.0)),
            price=float(payload["price"]) if "price" in payload and payload["price"] is not None else None,
        )


@dataclass(slots=True)
class Solution:
    status: str
    gap: float
    kpis: Dict[str, float]
    steps: List[SolutionStep]
    binding_constraints: List[str]
    activities: Dict[str, float]
    shadow_prices: Dict[str, float]

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "Solution":
        return Solution(
            status=str(payload.get("status", "UNKNOWN")),
            gap=float(payload.get("gap", 0.0)),
            kpis={key: float(value) for key, value in payload.get("kpis", {}).items()},
            steps=[SolutionStep.from_dict(item) for item in payload.get("steps", [])],
            binding_constraints=list(payload.get("binding_constraints", [])),
            activities={key: float(value) for key, value in payload.get("activities", {}).items()},
            shadow_prices={key: float(value) for key, value in payload.get("shadow_prices", {}).items()},
        )


@dataclass(slots=True)
class RobustEvaluation:
    worst_case_service: Optional[float] = None
    cvar_cost: Optional[float] = None
    stress_samples: Optional[int] = None

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "RobustEvaluation":
        return RobustEvaluation(
            worst_case_service=float(payload["worst_case_service"]) if payload.get("worst_case_service") is not None else None,
            cvar_cost=float(payload["cvar_cost"]) if payload.get("cvar_cost") is not None else None,
            stress_samples=int(payload["stress_samples"]) if payload.get("stress_samples") is not None else None,
        )


@dataclass(slots=True)
class SimulationSummary:
    runs: int
    mean_service: float
    p10_service: Optional[float] = None
    p90_service: Optional[float] = None
    avg_shortage: Optional[float] = None
    max_shortage: Optional[float] = None
    avg_leftover: Optional[float] = None
    avg_expedite_cost: Optional[float] = None

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "SimulationSummary":
        return SimulationSummary(
            runs=int(payload.get("runs", 0)),
            mean_service=float(payload.get("mean_service", 0.0)),
            p10_service=float(payload["p10_service"]) if payload.get("p10_service") is not None else None,
            p90_service=float(payload["p90_service"]) if payload.get("p90_service") is not None else None,
            avg_shortage=float(payload["avg_shortage"]) if payload.get("avg_shortage") is not None else None,
            max_shortage=float(payload["max_shortage"]) if payload.get("max_shortage") is not None else None,
            avg_leftover=float(payload["avg_leftover"]) if payload.get("avg_leftover") is not None else None,
            avg_expedite_cost=float(payload["avg_expedite_cost"]) if payload.get("avg_expedite_cost") is not None else None,
        )


@dataclass(slots=True)
class Diagnostics:
    reduction: Dict[str, Any] = field(default_factory=dict)
    robust_eval: Optional[RobustEvaluation] = None
    simulation: Optional[SimulationSummary] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "Diagnostics":
        raw_payload = dict(payload)
        return Diagnostics(
            reduction=dict(payload.get("reduction", {})),
            robust_eval=RobustEvaluation.from_dict(payload.get("robust_eval", {})) if payload.get("robust_eval") else None,
            simulation=SimulationSummary.from_dict(payload.get("simulation", {})) if payload.get("simulation") else None,
            raw=raw_payload,
        )


@dataclass(slots=True)
class PolicySnapshot:
    allow: bool
    policy_id: str
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    controls: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "PolicySnapshot":
        return PolicySnapshot(
            allow=bool(payload.get("allow", True)),
            policy_id=str(payload.get("policy_id", "policy.guard.v1")),
            reasons=list(payload.get("reasons", [])),
            warnings=list(payload.get("warnings", [])),
            controls=dict(payload.get("controls", {})),
        )


@dataclass(slots=True)
class KernelRunResult:
    evidence_ref: str
    scenario_set: Optional[ScenarioSet]
    optimodel: Optional[OptiModel]
    solution: Solution
    diagnostics: Diagnostics
    policy: Optional[PolicySnapshot]
    raw: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "KernelRunResult":
        return KernelRunResult(
            evidence_ref=str(payload.get("evidence_ref", "")),
            scenario_set=ScenarioSet.from_dict(payload["forecast"]) if payload.get("forecast") else None,
            optimodel=OptiModel.from_dict(payload["optimodel"]) if payload.get("optimodel") else None,
            solution=Solution.from_dict(payload.get("solution", {})),
            diagnostics=Diagnostics.from_dict(payload.get("diagnostics", {})),
            policy=PolicySnapshot.from_dict(payload.get("policy", {})) if payload.get("policy") else None,
            raw=dict(payload),
        )

*** End Patch
