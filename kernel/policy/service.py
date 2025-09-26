"""Policy guard service implementing governance & safety checks."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Mapping, Optional

from kernel.datamodel import (
    PlanningContext,
    PolicyDecision,
    PolicySnapshot,
    ScenarioSet,
    Solution,
    solution_to_dict,
)


class PolicyGuardService:
    """Evaluates GoalDSL + context against governance and safety policies."""

    DEFAULT_TIER_RULES: Dict[str, Dict[str, Optional[float]]] = {
        "free": {"max_scenarios": 40, "max_budget": 5_000.0},
        "standard": {"max_scenarios": 120, "max_budget": 25_000.0},
        "pro": {"max_scenarios": 220, "max_budget": 75_000.0},
        "enterprise": {"max_scenarios": None, "max_budget": None},
        "_default": {"max_scenarios": 120, "max_budget": 25_000.0},
    }

    def __init__(
        self,
        *,
        tier_rules: Optional[Mapping[str, Mapping[str, Optional[float]]]] = None,
    ) -> None:
        self.tier_rules: Dict[str, Dict[str, Optional[float]]] = {
            tier: dict(rules)
            for tier, rules in (tier_rules or self.DEFAULT_TIER_RULES).items()
        }

    def evaluate(
        self,
        goal: Any,
        context: PlanningContext,
        scenarios: ScenarioSet,
        *,
        tenant: Any = None,
    ) -> PolicyDecision:
        policies = getattr(goal, "policies", {}) or {}
        policy_id = policies.get("policy_id", "policy.guard.v1")
        tier = self._resolve_tier(policies, tenant)
        tier_limits = self.tier_rules.get(tier, self.tier_rules.get("_default", {}))

        allow = True
        reasons: List[str] = []
        warnings: List[str] = []
        controls: Dict[str, Any] = {
            "tier": tier,
        }

        if policies.get("deny"):
            allow = False
            deny_reasons = policies.get("deny_reasons") or ["policy deny flag"]
            reasons.extend(str(reason) for reason in deny_reasons)

        scenario_cap = self._resolve_cap(policies, tier_limits, "max_scenarios")
        if scenario_cap is not None:
            controls["scenario_cap"] = scenario_cap
            if scenarios.num_scenarios > scenario_cap:
                allow = False
                reasons.append(
                    f"scenario count {scenarios.num_scenarios} exceeds cap {scenario_cap} for tier {tier}"
                )
            elif scenarios.num_scenarios > 0.9 * scenario_cap:
                warnings.append(
                    f"scenario count {scenarios.num_scenarios} is within 10% of cap {scenario_cap} for tier {tier}"
                )

        budget_request = self._extract_budget(goal)
        budget_cap = self._resolve_cap(policies, tier_limits, "max_budget")
        if budget_cap is not None:
            controls["budget_cap"] = budget_cap
            if budget_request and budget_request > budget_cap:
                allow = False
                reasons.append(
                    f"requested budget {budget_request} exceeds allowed cap {budget_cap} for tier {tier}"
                )
            elif budget_request and budget_request > 0.85 * budget_cap:
                warnings.append(
                    f"budget request {budget_request} is within 15% of cap {budget_cap}"
                )

        controls.update(self._collect_goal_controls(goal))
        warnings.extend(self._detect_supplier_conflicts(policies, context))

        snapshot = PolicySnapshot(
            allow=allow,
            policy_id=policy_id,
            reasons=list(dict.fromkeys(reasons)),
            warnings=list(dict.fromkeys(warnings)),
            controls=controls,
        )
        return PolicyDecision(allow=allow, policy_snapshot=snapshot)

    def evaluate_solution(
        self,
        snapshot: PolicySnapshot,
        solution: Solution | Dict[str, Any],
        diagnostics: Mapping[str, Any],
    ) -> PolicySnapshot:
        solution_payload = solution
        if not isinstance(solution, dict):
            solution_payload = solution_to_dict(solution)

        kpis: Mapping[str, float] = solution_payload.get("kpis", {})  # type: ignore[arg-type]
        controls = snapshot.controls
        warnings = list(snapshot.warnings)
        reasons = list(snapshot.reasons)
        allow = snapshot.allow

        service_min = self._control_value(controls, "service_min")
        service_kpi = self._resolve_kpi(kpis, ("service", "service_level"))
        if service_min is not None:
            if service_kpi is not None and service_kpi < service_min:
                allow = False
                reasons.append(
                    f"service KPI {service_kpi} below policy minimum {service_min}"
                )
            else:
                robust_eval = diagnostics.get("robust_eval", {}) if diagnostics else {}
                worst_case_service = robust_eval.get("worst_case_service")
                if (
                    isinstance(worst_case_service, (int, float))
                    and worst_case_service < service_min
                ):
                    warnings.append(
                        f"robust worst_case_service {worst_case_service} below policy minimum {service_min}"
                    )

        budget_cap = self._control_value(controls, "budget_cap")
        total_cost = self._resolve_kpi(kpis, ("total_cost", "cost"))
        if budget_cap is not None and total_cost is not None and total_cost > budget_cap:
            allow = False
            reasons.append(
                f"total_cost {total_cost} exceeds budget cap {budget_cap}"
            )

        snapshot.allow = allow
        snapshot.reasons = list(dict.fromkeys(reasons))
        snapshot.warnings = list(dict.fromkeys(warnings))
        snapshot.controls = controls
        return snapshot

    @staticmethod
    def _resolve_tier(policies: Mapping[str, Any], tenant: Any) -> str:
        tier = None
        if tenant is not None:
            tier = getattr(tenant, "tier", None) or getattr(tenant, "get", lambda *_: None)("tier")
        return str(policies.get("tier", tier or "standard")).lower()

    @staticmethod
    def _resolve_cap(
        policies: Mapping[str, Any],
        tier_limits: Mapping[str, Optional[float]],
        key: str,
    ) -> Optional[float]:
        caps = policies.get("caps", {}) if isinstance(policies, Mapping) else {}
        override = caps.get(key)
        if override is not None:
            try:
                return float(override)
            except (TypeError, ValueError):
                return None
        limit = tier_limits.get(key)
        return float(limit) if limit is not None else None

    @staticmethod
    def _extract_budget(goal: Any) -> Optional[float]:
        constraints = getattr(goal, "constraints", {}) or {}
        if isinstance(constraints, Mapping):
            budget = constraints.get("budget_month")
            try:
                return float(budget) if budget is not None else None
            except (TypeError, ValueError):
                return None
        return None

    @staticmethod
    def _collect_goal_controls(goal: Any) -> Dict[str, Any]:
        controls: Dict[str, Any] = {}
        constraints = getattr(goal, "constraints", {}) or {}
        if isinstance(constraints, Mapping) and "service_min" in constraints:
            try:
                controls["service_min"] = float(constraints["service_min"])
            except (TypeError, ValueError):
                pass
        policies = getattr(goal, "policies", {}) or {}
        controls["policy_flags"] = [key for key, value in policies.items() if value and key not in {"caps", "deny", "deny_reasons"}]
        return controls

    @staticmethod
    def _detect_supplier_conflicts(policies: Mapping[str, Any], context: PlanningContext) -> List[str]:
        warnings: List[str] = []
        blocklist: Iterable[str] = policies.get("vendor_blocklist", []) if isinstance(policies, Mapping) else []
        block_set = {str(v) for v in blocklist}
        if not block_set:
            return warnings
        for sku_ctx in context.skus:
            for supplier in sku_ctx.supplier_options:
                if supplier.supplier_id in block_set:
                    warnings.append(
                        f"supplier {supplier.supplier_id} present in context but listed in vendor_blocklist"
                    )
        return warnings

    @staticmethod
    def _control_value(controls: Mapping[str, Any], key: str) -> Optional[float]:
        value = controls.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _resolve_kpi(kpis: Mapping[str, Any], keys: Iterable[str]) -> Optional[float]:
        for key in keys:
            value = kpis.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    def snapshot_to_dict(self, snapshot: PolicySnapshot) -> Dict[str, Any]:
        """Expose dataclass conversion for serialization callers."""
        return asdict(snapshot)
