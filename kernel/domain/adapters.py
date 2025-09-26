"""Domain-specific adapters for vertical customization."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from kernel.datamodel import PlanningContext, SKUContext, SupplierOption


@dataclass
class DomainAdapter:
    """Base class for domain adapters capable of tweaking goal DSL and context."""

    name: str = ""

    def prepare_goal(self, goaldsl: Any) -> Any:  # pragma: no cover - default no-op
        return goaldsl

    def prepare_context(self, context: PlanningContext) -> PlanningContext:  # pragma: no cover
        return context

    def postprocess_solution(self, result: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        return result


@dataclass
class RetailDomainAdapter(DomainAdapter):
    """Retail/Grocery adapter ensuring waste objective and shelf-life metadata."""

    name: str = "retail"
    waste_weight: float = 0.15

    def prepare_goal(self, goaldsl: Mapping[str, Any] | str) -> Any:
        if isinstance(goaldsl, str):
            return goaldsl
        goal_copy = copy.deepcopy(goaldsl)
        objective = goal_copy.setdefault("objective", {})
        objective.setdefault("waste", self.waste_weight)
        constraints = goal_copy.setdefault("constraints", {})
        constraints.setdefault("service_min", 0.95)
        return goal_copy

    def prepare_context(self, context: PlanningContext) -> PlanningContext:
        cloned_skus = []
        for sku_ctx in context.skus:
            sku_clone = SKUContext(
                sku=sku_ctx.sku,
                demand_baseline=dict(sku_ctx.demand_baseline),
                supplier_options=[
                    SupplierOption(
                        supplier_id=opt.supplier_id,
                        price=opt.price,
                        moq=opt.moq,
                        lead_time_days=opt.lead_time_days,
                        co2_per_unit=opt.co2_per_unit,
                        capacity=opt.capacity,
                    )
                    for opt in sku_ctx.supplier_options
                ],
            )
            cloned_skus.append(sku_clone)
        return PlanningContext(
            horizon=context.horizon,
            periods=context.periods,
            locations=context.locations,
            skus=cloned_skus,
        )

    def postprocess_solution(self, result: Dict[str, Any]) -> Dict[str, Any]:
        steps = result.get("solution", {}).get("steps", [])
        waste_annotation = sum(step.get("quantity", 0.0) * 0.02 for step in steps)
        result.setdefault("diagnostics", {}).setdefault("domain", {})[
            "estimated_waste"
        ] = round(waste_annotation, 3)
        return result


@dataclass
class ManufacturingDomainAdapter(DomainAdapter):
    """Manufacturing adapter enforcing lead time and setup penalties."""

    name: str = "manufacturing"
    setup_penalty: float = 50.0

    def prepare_goal(self, goaldsl: Mapping[str, Any] | str) -> Any:
        if isinstance(goaldsl, str):
            return goaldsl
        goal_copy = copy.deepcopy(goaldsl)
        constraints = goal_copy.setdefault("constraints", {})
        constraints.setdefault("lead_time_cap", 10)
        objective = goal_copy.setdefault("objective", {})
        objective.setdefault("setup_cost", self.setup_penalty)
        return goal_copy

    def prepare_context(self, context: PlanningContext) -> PlanningContext:
        cloned_skus = []
        for sku_ctx in context.skus:
            supplier_options = []
            for opt in sku_ctx.supplier_options:
                supplier_options.append(
                    SupplierOption(
                        supplier_id=opt.supplier_id,
                        price=opt.price,
                        moq=max(opt.moq, 5),
                        lead_time_days=min(opt.lead_time_days, 10),
                        co2_per_unit=opt.co2_per_unit,
                        capacity=opt.capacity,
                    )
                )
            cloned_skus.append(
                SKUContext(
                    sku=sku_ctx.sku,
                    demand_baseline=dict(sku_ctx.demand_baseline),
                    supplier_options=supplier_options,
                )
            )
        return PlanningContext(
            horizon=context.horizon,
            periods=context.periods,
            locations=context.locations,
            skus=cloned_skus,
        )

    def postprocess_solution(self, result: Dict[str, Any]) -> Dict[str, Any]:
        domain_diag = result.setdefault("diagnostics", {}).setdefault("domain", {})
        domain_diag["setup_runs"] = len(result.get("solution", {}).get("steps", []))
        return result


@dataclass
class HealthcareDomainAdapter(DomainAdapter):
    """Healthcare adapter emphasizing staffing and expiry controls."""

    name: str = "healthcare"
    service_floor: float = 0.97

    def prepare_goal(self, goaldsl: Mapping[str, Any] | str) -> Any:
        if isinstance(goaldsl, str):
            return goaldsl
        goal_copy = copy.deepcopy(goaldsl)
        constraints = goal_copy.setdefault("constraints", {})
        constraints.setdefault("service_min", self.service_floor)
        constraints.setdefault("expiry_waste", 0.02)
        objective = goal_copy.setdefault("objective", {})
        objective.setdefault("staff_coverage", 0.25)
        return goal_copy

    def postprocess_solution(self, result: Dict[str, Any]) -> Dict[str, Any]:
        diagnostics = result.setdefault("diagnostics", {}).setdefault("domain", {})
        diagnostics["on_call_shifts"] = len(result.get("solution", {}).get("steps", []))
        return result


@dataclass
class LogisticsDomainAdapter(DomainAdapter):
    """Logistics adapter prioritizing CO₂ and on-time service."""

    name: str = "logistics"

    def prepare_goal(self, goaldsl: Mapping[str, Any] | str) -> Any:
        if isinstance(goaldsl, str):
            return goaldsl
        goal_copy = copy.deepcopy(goaldsl)
        objective = goal_copy.setdefault("objective", {})
        objective.setdefault("co2", 0.4)
        objective.setdefault("on_time", 0.3)
        constraints = goal_copy.setdefault("constraints", {})
        constraints.setdefault("co2_cap", 300)
        constraints.setdefault("on_time_min", 0.98)
        return goal_copy

    def postprocess_solution(self, result: Dict[str, Any]) -> Dict[str, Any]:
        diagnostics = result.setdefault("diagnostics", {}).setdefault("domain", {})
        diagnostics["route_segments"] = len(result.get("solution", {}).get("steps", []))
        return result


@dataclass
class HospitalityDomainAdapter(DomainAdapter):
    """Hospitality adapter focusing on freshness and labor balance."""

    name: str = "hospitality"

    def prepare_goal(self, goaldsl: Mapping[str, Any] | str) -> Any:
        if isinstance(goaldsl, str):
            return goaldsl
        goal_copy = copy.deepcopy(goaldsl)
        objective = goal_copy.setdefault("objective", {})
        objective.setdefault("freshness", 0.3)
        constraints = goal_copy.setdefault("constraints", {})
        constraints.setdefault("prep_labor_max", 480)
        return goal_copy

    def postprocess_solution(self, result: Dict[str, Any]) -> Dict[str, Any]:
        diagnostics = result.setdefault("diagnostics", {}).setdefault("domain", {})
        diagnostics["freshness_score"] = round(0.9, 3)
        return result


def get_adapter(name: Optional[str]) -> Optional[DomainAdapter]:
    if not name:
        return None
    registry: Dict[str, DomainAdapter] = {
        "retail": RetailDomainAdapter(),
        "manufacturing": ManufacturingDomainAdapter(),
        "healthcare": HealthcareDomainAdapter(),
        "logistics": LogisticsDomainAdapter(),
        "hospitality": HospitalityDomainAdapter(),
    }
    return registry.get(name.lower())
