"""OptiGuide compiler producing OptiModel IR and explainability hints."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Tuple

from kernel.datamodel import (
    ConstraintDef,
    ExplainabilityHints,
    ObjectiveTerm,
    PolicyDecision,
    OptiModel,
    PlanningContext,
    RobustConfig,
    ScenarioSet,
    VariableDef,
)
from kernel.policy.service import PolicyGuardService


@dataclass
class GoalDSL:
    objective: Mapping[str, float]
    constraints: Mapping[str, Any]
    scope: Mapping[str, Any]
    policies: Mapping[str, Any]


class GoalDSLParser:
    """Parses GoalDSL JSON payloads into a normalized structure."""

    @staticmethod
    def parse(payload: Any) -> GoalDSL:
        if isinstance(payload, GoalDSL):
            return payload
        if isinstance(payload, str):
            data = json.loads(payload)
        elif isinstance(payload, Mapping):
            data = dict(payload)
        else:
            raise TypeError("GoalDSL payload must be str or mapping")
        return GoalDSL(
            objective=data.get("objective", {}),
            constraints=data.get("constraints", {}),
            scope=data.get("scope", {}),
            policies=data.get("policies", {}),
        )


class OptiGuideService:
    """Compiles GoalDSL + context + scenarios into OptiModel IR."""

    def __init__(self, policy_guard: PolicyGuardService | None = None) -> None:
        self.policy_guard = policy_guard or PolicyGuardService()

    def compile(
        self,
        goaldsl: Any,
        context: PlanningContext,
        scenarios: ScenarioSet,
        *,
        tenant: Any = None,
    ) -> Dict[str, Any]:
        goal = GoalDSLParser.parse(goaldsl)

        policy_decision = self._evaluate_policies(goal, context, scenarios, tenant=tenant)
        if not policy_decision.allow:
            raise ValueError(
                "Policy denied",
                {
                    "reasons": policy_decision.policy_snapshot.reasons,
                    "policy_id": policy_decision.policy_snapshot.policy_id,
                },
            )

        model = self._build_model(goal, context, scenarios)
        hints = self._build_explainability(goal)

        compiled_inputs = self._export_compiled_inputs(goal, context, scenarios)
        policy_snapshot = policy_decision.policy_snapshot

        return {
            "optimodel": model,
            "hints": hints,
            "metadata": {
                "goal_scope": goal.scope,
                "scenario_ids": [scenario.id for scenario in scenarios.scenarios],
                "policy_snapshot": asdict(policy_snapshot),
            },
            "compiled_inputs": compiled_inputs,
            "policy_snapshot": policy_snapshot,
        }

    def _build_model(
        self,
        goal: GoalDSL,
        context: PlanningContext,
        scenarios: ScenarioSet,
    ) -> OptiModel:
        variables = self._build_variables(context, scenarios)
        objective_terms = self._build_objective(goal, context)
        constraints = self._build_constraints(goal, context, scenarios)
        robust = self._robust_config(goal, scenarios)
        return OptiModel(
            vars=variables,
            objective_sense="min",
            objective_terms=objective_terms,
            constraints=constraints,
            robust=robust,
        )

    def _build_variables(
        self,
        context: PlanningContext,
        scenarios: ScenarioSet,
    ) -> Dict[str, VariableDef]:
        vars_dict: Dict[str, VariableDef] = {}
        vars_dict["x[sku,supplier,period,scenario]"] = VariableDef(
            name="order_quantity",
            vartype="continuous",
            lower_bound=0.0,
        )
        vars_dict["inv[sku,period,scenario]"] = VariableDef(
            name="inventory",
            vartype="continuous",
            lower_bound=0.0,
        )
        vars_dict["y[sku,supplier]"] = VariableDef(
            name="supplier_select",
            vartype="binary",
            lower_bound=0.0,
            upper_bound=1.0,
        )
        vars_dict["slack[constraint]"] = VariableDef(
            name="constraint_slack",
            vartype="continuous",
            lower_bound=0.0,
        )
        return vars_dict

    def _build_objective(
        self,
        goal: GoalDSL,
        context: PlanningContext,
    ) -> List[ObjectiveTerm]:
        objective_terms: List[ObjectiveTerm] = []
        objective_weights = goal.objective or {"cost": 1.0}
        objective_terms.append(
            ObjectiveTerm(
                name="cost",
                weight=float(objective_weights.get("cost", 1.0)),
                expression="sum(price[sku,supplier] * x[sku,supplier,period,scenario])",
            )
        )
        if objective_weights.get("service"):
            objective_terms.append(
                ObjectiveTerm(
                    name="service",
                    weight=float(objective_weights["service"]),
                    expression="- sum(fill_rate[sku,period])",
                )
            )
        if objective_weights.get("co2"):
            objective_terms.append(
                ObjectiveTerm(
                    name="co2",
                    weight=float(objective_weights["co2"]),
                    expression="sum(co2_per_unit[sku,supplier] * x[sku,supplier,period,scenario])",
                )
            )
        return objective_terms

    def _build_constraints(
        self,
        goal: GoalDSL,
        context: PlanningContext,
        scenarios: ScenarioSet,
    ) -> List[ConstraintDef]:
        constraints: List[ConstraintDef] = []
        goal_constraints = goal.constraints or {}
        if "budget_month" in goal_constraints:
            constraints.append(
                ConstraintDef(
                    name="budget_month",
                    expression="sum(price * x) <= budget_month",
                )
            )
        if "service_min" in goal_constraints:
            constraints.append(
                ConstraintDef(
                    name="service_min",
                    expression="fill_rate[sku,period] >= service_min",
                )
            )
        constraints.append(
            ConstraintDef(
                name="inventory_balance",
                expression="inv[t] = inv[t-1] + sum(x) - demand[scenario]",
            )
        )
        constraints.append(
            ConstraintDef(
                name="moq",
                expression="x >= moq * y",
            )
        )
        constraints.append(
            ConstraintDef(
                name="capacity",
                expression="sum(x[sku,supplier,period]) <= capacity[supplier,period]",
            )
        )
        if goal.policies.get("vendor_blocklist"):
            constraints.append(
                ConstraintDef(
                    name="vendor_block",
                    expression="y[v] = 0 for v in vendor_blocklist",
                )
            )
        return constraints

    def _build_explainability(self, goal: GoalDSL) -> ExplainabilityHints:
        track = ["budget", "moq", "balance", "lead_time"]
        sensitivities = ["price", "moq"]
        if goal.objective.get("co2"):
            track.append("co2")
            sensitivities.append("co2")
        return ExplainabilityHints(track=list(dict.fromkeys(track)), sensitivities=list(dict.fromkeys(sensitivities)))

    def _robust_config(self, goal: GoalDSL, scenarios: ScenarioSet) -> RobustConfig:
        robust_config = goal.constraints.get("robust") if isinstance(goal.constraints, dict) else None
        if isinstance(robust_config, dict):
            mode = robust_config.get("mode", "p95")
            if mode not in {"p95", "dro_wasserstein", "conformal"}:
                raise ValueError(f"Unsupported robust mode: {mode}")
            aggregation = {
                "p95": "p95",
                "dro_wasserstein": "cvar",
                "conformal": "quantile_interval",
            }[mode]
            return RobustConfig(
                scenarios=scenarios.num_scenarios,
                aggregation=aggregation,
            )
        return RobustConfig(
            scenarios=scenarios.num_scenarios,
            aggregation="p95",
        )

    def _export_compiled_inputs(
        self,
        goal: GoalDSL,
        context: PlanningContext,
        scenarios: ScenarioSet,
    ) -> Dict[str, Any]:
        prices: Dict[str, Dict[str, float]] = {}
        co2: Dict[str, Dict[str, float]] = {}
        moq: Dict[str, Dict[str, float]] = {}
        capacity: Dict[str, Dict[str, float]] = {}
        lead_times: Dict[str, Dict[str, float]] = {}

        moq_policy = goal.policies.get("moq_overrides", {})
        blocklist = set(goal.policies.get("vendor_blocklist", []))

        for sku_ctx in context.skus:
            prices[sku_ctx.sku] = {}
            co2[sku_ctx.sku] = {}
            moq[sku_ctx.sku] = {}
            capacity[sku_ctx.sku] = {}
            lead_times[sku_ctx.sku] = {}
            for supplier in sku_ctx.supplier_options:
                prices[sku_ctx.sku][supplier.supplier_id] = supplier.price
                co2[sku_ctx.sku][supplier.supplier_id] = supplier.co2_per_unit
                override_value = moq_policy.get(sku_ctx.sku)
                moq_value = override_value if override_value is not None else supplier.moq
                moq[sku_ctx.sku][supplier.supplier_id] = float(moq_value)
                capacity_value = supplier.capacity if supplier.capacity is not None else float("inf")
                capacity[sku_ctx.sku][supplier.supplier_id] = capacity_value
                lead_times[sku_ctx.sku][supplier.supplier_id] = supplier.lead_time_days

        scenario_demand = {
            scenario.id: scenario.demand for scenario in scenarios.scenarios
        }
        scenario_lead_time = {
            scenario.id: scenario.lead_time_days for scenario in scenarios.scenarios
        }

        return {
            "prices": prices,
            "co2": co2,
            "moq": moq,
            "capacity": capacity,
            "lead_times": lead_times,
            "scenario_demand": scenario_demand,
            "scenario_lead_time": scenario_lead_time,
            "constraints": goal.constraints,
            "objective": goal.objective,
            "vendor_blocklist": list(blocklist),
        }

    def _evaluate_policies(
        self,
        goal: GoalDSL,
        context: PlanningContext,
        scenarios: ScenarioSet,
        *,
        tenant: Any = None,
    ) -> PolicyDecision:
        return self.policy_guard.evaluate(goal, context, scenarios, tenant=tenant)
