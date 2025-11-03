from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from packages.kernel_common import load_schema
from packages.kernel_common.deps import require_auth
from packages.kernel_common.logging import configure_logging

try:
    from ortools.linear_solver import pywraplp

    HAS_SOLVER = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_SOLVER = False
    pywraplp = None

try:
    import pyomo.environ as pyo
    from pyomo.opt import SolverStatus, TerminationCondition

    HAS_PYOMO = True
except ImportError:  # pragma: no cover - optional dependency
    HAS_PYOMO = False
    pyo = None
    SolverStatus = None
    TerminationCondition = None

logger = configure_logging("optimiser-service")

app = FastAPI(
    title="Dyocense Optimiser Service",
    version="0.6.0",
    description="Optimiser powered by OR-Tools or Pyomo backends with a deterministic fallback when unavailable.",
)


class OptimiseRequest(BaseModel):
    ops: dict = Field(..., description="Validated OPS document.")
    warm_start: Optional[dict] = Field(
        default=None,
        description="Optional prior SolutionPack used for warm-starting and KPI validation.",
    )


class OptimiseResponse(BaseModel):
    solution: dict = Field(
        ..., description="SolutionPack JSON document produced by the optimiser."
    )
    schema: dict = Field(
        default_factory=lambda: load_schema("solution_pack.schema.json"),
        description="Inline SolutionPack schema snapshot.",
    )


@app.post("/v1/optimise", response_model=OptimiseResponse)
def optimise(body: OptimiseRequest, identity: dict = Depends(require_auth)) -> OptimiseResponse:
    """
    Optimise using OR-Tools when available, otherwise return deterministic fallback.
    """
    ops = body.ops
    if "metadata" not in ops:
        raise HTTPException(status_code=400, detail="OPS metadata missing.")

    solution_pack = optimise_ops_document(ops, warm_start=body.warm_start)

    logger.info(
        "Produced solution with %d decision entries (tenant=%s)",
        sum(len(v) if isinstance(v, dict) else 1 for v in solution_pack["decisions"].values()),
        identity["tenant_id"],
    )
    return OptimiseResponse(solution=solution_pack)


def optimise_ops_document(ops: dict, warm_start: Optional[dict] = None) -> dict:
    backend = os.getenv("OPTIMISER_BACKEND", "ortools").lower()
    if backend == "pyomo":
        if HAS_PYOMO:
            try:
                solution = _solve_with_pyomo(ops, warm_start=warm_start)
                return _annotate_warm_start(solution, ops, warm_start)
            except Exception as exc:  # pragma: no cover - fallback path
                logger.warning("Pyomo solver failed (%s). Falling back to OR-Tools.", exc)
        else:
            logger.warning("OPTIMISER_BACKEND=pyomo but Pyomo is not installed. Falling back to OR-Tools.")

    if HAS_SOLVER:
        try:
            solution = _solve_with_ortools(ops, warm_start=warm_start)
            return _annotate_warm_start(solution, ops, warm_start)
        except Exception as exc:  # pragma: no cover - fall back to stub
            logger.warning("OR-Tools solver failed (%s). Falling back to stub.", exc)
    else:
        logger.warning("OR-Tools not installed. Attempting Pyomo backend.")
        if HAS_PYOMO:
            try:
                solution = _solve_with_pyomo(ops, warm_start=warm_start)
                return _annotate_warm_start(solution, ops, warm_start)
            except Exception as exc:  # pragma: no cover
                logger.warning("Pyomo fallback failed (%s).", exc)
        else:
            logger.warning("Pyomo not installed. Using stub optimiser.")
    solution = _stub_solution(ops)
    return _annotate_warm_start(solution, ops, warm_start)


def _stub_solution(ops: dict) -> dict:
    demand = ops.get("parameters", {}).get("demand", {})
    decisions = {"stock": {sku: float(quantity) for sku, quantity in demand.items()}}
    cost = _compute_linear_cost(ops, decisions["stock"])
    return _construct_solution(
        ops=ops,
        solver_name="stub-optimiser",
        decisions=decisions,
        objective_value=cost,
        status_text="optimal",
        notes=["Fallback stub solution used"],
    )


def _construct_solution(
    ops: dict,
    solver_name: str,
    decisions: dict,
    objective_value: float,
    status_text: str,
    notes: Optional[list[str]] = None,
) -> dict:
    metadata = ops.get("metadata", {})
    return {
        "metadata": {
            "ops_version": metadata.get("ops_version", "1.0.0"),
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "solver": solver_name,
            "run_id": metadata.get("project_id", "phase-run"),
            "archetype_id": metadata.get("archetype_id"),
            "objective": ops.get("objective"),
        },
        "decisions": decisions,
        "kpis": {
            "objective_value": objective_value,
            "total_holding_cost": objective_value,
        },
        "diagnostics": {
            "status": status_text,
            "notes": notes or [],
        },
    }


def _infer_indices(parameters: dict, set_name: str) -> list:
    indices = []
    candidate = parameters.get(set_name)
    if isinstance(candidate, dict):
        indices = list(candidate.keys())
    elif isinstance(candidate, list):
        indices = list(range(len(candidate)))
    if not indices and "demand" in parameters and isinstance(parameters["demand"], dict):
        indices = list(parameters["demand"].keys())
    return indices


def _coefficient_for_meta(meta_entry: Dict[str, Optional[str]], coeffs: dict) -> float:
    base = meta_entry["base"]
    idx = meta_entry["index"]
    if idx is not None:
        return float(coeffs.get(idx, 0.0))
    return float(coeffs.get(base, coeffs.get("default", 0.0)))


def _annotate_warm_start(solution: dict, ops: dict, warm_start: Optional[dict]) -> dict:
    if not warm_start:
        return solution

    warm_decisions = warm_start.get("decisions") or {}
    warm_objective = _compute_objective_from_decisions(ops, warm_decisions)
    sense = (ops.get("objective", {}).get("sense") or "min").lower()
    objective_value = solution.get("kpis", {}).get("objective_value")
    improvement = None
    if objective_value is not None and warm_objective is not None:
        if sense == "min":
            improvement = float(objective_value) <= float(warm_objective) + 1e-6
        else:
            improvement = float(objective_value) >= float(warm_objective) - 1e-6

    diagnostics = solution.setdefault("diagnostics", {})
    notes = diagnostics.setdefault("notes", [])
    if warm_objective is not None:
        diagnostics["warm_start"] = {
            "objective_warm_start": warm_objective,
            "objective_new": objective_value,
            "improved": improvement,
            "sense": sense,
        }
        if improvement is False:
            notes.append("Warm-start validation detected regression in objective value")
    else:
        diagnostics["warm_start"] = {
            "objective_warm_start": None,
            "objective_new": objective_value,
            "improved": None,
            "sense": sense,
        }
        notes.append("Warm-start objective could not be computed; check holding_cost parameters")
    return solution


def _compute_objective_from_decisions(ops: dict, decisions: dict) -> Optional[float]:
    if not decisions:
        return None
    coeffs = ops.get("parameters", {}).get("holding_cost")
    if not isinstance(coeffs, dict):
        return None
    total = 0.0
    for var_name, bucket in decisions.items():
        if isinstance(bucket, dict):
            for index, value in bucket.items():
                coeff = coeffs.get(index)
                if coeff is None:
                    coeff = coeffs.get(var_name)
                if coeff is None:
                    coeff = coeffs.get("default")
                if coeff is None:
                    return None
                total += float(coeff) * float(value)
        else:
            coeff = coeffs.get(var_name) or coeffs.get("default")
            if coeff is None:
                return None
            total += float(coeff) * float(bucket)
    return total


def _pyomo_domain(var_type: str):
    if pyo is None:
        raise RuntimeError("Pyomo is not available")
    if var_type == "binary":
        return pyo.Binary
    if var_type == "integer":
        return pyo.Integers
    return pyo.Reals


def _pyomo_bounds(lb: float, ub: Optional[float], var_type: str) -> Optional[tuple[Optional[float], Optional[float]]]:
    if var_type == "binary":
        return (0.0, 1.0)
    lower = lb
    upper = None if ub is None or math.isinf(ub) else ub
    return (lower, upper)


def _get_warm_start_value(warm_start: dict, base_name: str, index: Optional[str]) -> Optional[float]:
    decisions = warm_start.get("decisions") or {}
    values = decisions.get(base_name)
    if values is None:
        return None
    if isinstance(values, dict):
        key = str(index) if index is not None else index
        if key in values:
            return float(values[key])
        # fallback to non-str keys
        if index in values:
            return float(values[index])
        return None
    if index is None:
        return float(values)
    return None


def _set_pyomo_warm_start(var, warm_start: dict, base_name: str, index: Optional[str]) -> None:
    value = _get_warm_start_value(warm_start, base_name, index)
    if value is not None:
        try:
            var.value = value
        except Exception:  # pragma: no cover - varies by domain bounds
            logger.debug("Unable to apply Pyomo warm-start for %s[%s]", base_name, index)


def _set_ortools_hint(var, warm_start: dict, base_name: str, index: Optional[str]) -> None:
    value = _get_warm_start_value(warm_start, base_name, index)
    if value is not None:
        try:
            var.SetHint(value)
        except Exception:  # pragma: no cover
            logger.debug("Unable to set OR-Tools hint for %s[%s]", base_name, index)


def _solve_with_pyomo(ops: dict, warm_start: Optional[dict] = None) -> dict:
    if not HAS_PYOMO or pyo is None:
        raise RuntimeError("Pyomo backend not available")

    model = pyo.ConcreteModel()
    parameters = ops.get("parameters", {})
    variables: Dict[str, pyo.Var] = {}
    meta: Dict[str, Dict[str, Optional[str]]] = {}

    for var_def in ops.get("decision_variables", []):
        base_name = var_def["name"]
        lb = float(var_def.get("lb", 0.0))
        ub = var_def.get("ub")
        ub_val = float(ub) if ub is not None else None
        var_type = var_def.get("type", "continuous")
        index_sets = var_def.get("index_sets") or []
        domain = _pyomo_domain(var_type)
        bounds = _pyomo_bounds(lb, ub_val, var_type)

        if index_sets:
            set_name = index_sets[0]
            indices = _infer_indices(parameters, set_name)
            if not indices:
                raise HTTPException(status_code=400, detail=f"No indices found for set '{set_name}'")
            index_component = pyo.Set(initialize=indices, ordered=True)
            model.add_component(f"{base_name}_index", index_component)
            var_component = pyo.Var(index_component, domain=domain, bounds=bounds)
            model.add_component(base_name, var_component)
            for index in indices:
                var_name = f"{base_name}[{index}]"
                variables[var_name] = var_component[index]
                meta[var_name] = {"base": base_name, "index": index}
                if warm_start:
                    _set_pyomo_warm_start(var_component[index], warm_start, base_name, index)
        else:
            var_component = pyo.Var(domain=domain, bounds=bounds)
            model.add_component(base_name, var_component)
            variables[base_name] = var_component
            meta[base_name] = {"base": base_name, "index": None}
            if warm_start:
                _set_pyomo_warm_start(var_component, warm_start, base_name, None)

    coeffs = parameters.get("holding_cost", {})
    sense = ops.get("objective", {}).get("sense", "min")
    objective_expr = sum(_coefficient_for_meta(meta[name], coeffs) * var for name, var in variables.items())
    if sense == "min":
        model.objective = pyo.Objective(expr=objective_expr, sense=pyo.minimize)
    else:
        model.objective = pyo.Objective(expr=objective_expr, sense=pyo.maximize)

    model.constraints = pyo.ConstraintList()
    for constraint in ops.get("constraints", []):
        _apply_constraint_pyomo(model, variables, meta, parameters, constraint)

    solver_name = os.getenv("PYOMO_SOLVER", "cbc")
    solver = pyo.SolverFactory(solver_name)
    if solver is None or not solver.available(False):  # pragma: no cover - external solver
        raise RuntimeError(f"Pyomo solver '{solver_name}' is not available")

    results = solver.solve(model, tee=False)
    if results.solver.status not in {SolverStatus.ok, SolverStatus.warning}:
        raise RuntimeError(f"Solver status {results.solver.status}")  # pragma: no cover

    termination = results.solver.termination_condition
    status_map = {
        TerminationCondition.optimal: "optimal",
        TerminationCondition.locallyOptimal: "optimal",
        TerminationCondition.feasible: "feasible",
        TerminationCondition.infeasible: "infeasible",
        TerminationCondition.unbounded: "unbounded",
    }
    status_text = status_map.get(termination, "unknown")

    if termination not in {
        TerminationCondition.optimal,
        TerminationCondition.locallyOptimal,
        TerminationCondition.feasible,
    }:
        raise RuntimeError(f"Pyomo solver did not converge ({termination})")

    decisions: Dict[str, Dict[str, float] | float] = {}
    for name, var in variables.items():
        base = meta[name]["base"]
        idx = meta[name]["index"]
        value = float(pyo.value(var))
        if idx is None:
            decisions[base] = value
        else:
            bucket = decisions.setdefault(base, {})
            assert isinstance(bucket, dict)
            bucket[idx] = value

    objective_value = float(pyo.value(model.objective))
    return _construct_solution(
        ops=ops,
        solver_name=f"pyomo-{solver_name}",
        decisions=decisions,
        objective_value=objective_value,
        status_text=status_text,
        notes=["Solved with Pyomo"],
    )


def _solve_with_ortools(ops: dict, warm_start: Optional[dict] = None) -> dict:
    if pywraplp is None:
        raise RuntimeError("OR-Tools not available")

    solver = pywraplp.Solver.CreateSolver("CBC_MIXED_INTEGER_PROGRAMMING")
    if solver is None:
        raise RuntimeError("Failed to create OR-Tools solver")

    parameters = ops.get("parameters", {})

    variables: Dict[str, pywraplp.Variable] = {}
    meta: Dict[str, Dict[str, Optional[str]]] = {}

    for var_def in ops.get("decision_variables", []):
        base_name = var_def["name"]
        lb = float(var_def.get("lb", 0.0))
        ub = float(var_def.get("ub", solver.infinity()))
        var_type = var_def.get("type", "continuous")
        index_sets = var_def.get("index_sets") or []

        def create_var(name: str):
            if var_type == "binary":
                return solver.IntVar(0.0, 1.0, name)
            if var_type == "integer":
                return solver.IntVar(lb, ub, name)
            return solver.NumVar(lb, ub, name)

        if index_sets:
            set_name = index_sets[0]
            indices = _infer_indices(parameters, set_name)
            if not indices:
                raise HTTPException(status_code=400, detail=f"No indices found for set '{set_name}'")
            for index in indices:
                var_name = f"{base_name}[{index}]"
                variables[var_name] = create_var(var_name)
                meta[var_name] = {"base": base_name, "index": index}
                if warm_start:
                    _set_ortools_hint(variables[var_name], warm_start, base_name, index)
        else:
            variables[base_name] = create_var(base_name)
            meta[base_name] = {"base": base_name, "index": None}
            if warm_start:
                _set_ortools_hint(variables[base_name], warm_start, base_name, None)

    objective = solver.Objective()
    sense = ops.get("objective", {}).get("sense", "min")
    coeffs = parameters.get("holding_cost", {})
    for name, var in variables.items():
        coeff = _coefficient_for_meta(meta[name], coeffs)
        objective.SetCoefficient(var, coeff)
    if sense == "min":
        objective.SetMinimization()
    else:
        objective.SetMaximization()

    for constraint in ops.get("constraints", []):
        _apply_constraint(solver, variables, meta, parameters, constraint)

    status = solver.Solve()
    status_map = {
        pywraplp.Solver.OPTIMAL: "optimal",
        pywraplp.Solver.FEASIBLE: "feasible",
        pywraplp.Solver.INFEASIBLE: "infeasible",
        pywraplp.Solver.UNBOUNDED: "unbounded",
    }
    status_text = status_map.get(status, "unknown")

    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        raise HTTPException(status_code=500, detail=f"Solver failed ({status_text})")

    decisions: Dict[str, Dict[str, float] | float] = {}
    for name, var in variables.items():
        base = meta[name]["base"]
        idx = meta[name]["index"]
        value = float(var.solution_value())
        if idx is None:
            decisions[base] = value
        else:
            bucket = decisions.setdefault(base, {})
            assert isinstance(bucket, dict)
            bucket[idx] = value

    objective_value = solver.Objective().Value()
    return _construct_solution(
        ops=ops,
        solver_name="cbc-mip",
        decisions=decisions,
        objective_value=objective_value,
        status_text=status_text,
        notes=["Solved with OR-Tools CBC"],
    )


def _apply_constraint(solver, variables, meta, parameters, constraint):
    expression = constraint.get("expression")
    if not expression:
        return

    operators = [">=", "<=", "=="]
    operator_used = None
    for op in operators:
        if op in expression:
            operator_used = op
            left, right = expression.split(op)
            break
    if not operator_used:
        raise HTTPException(status_code=400, detail=f"Unsupported constraint expression '{expression}'")

    left = left.strip()
    right = right.strip()
    for_all = constraint.get("for_all")

    if for_all:
        indices = _infer_indices(parameters, for_all)
        if not indices:
            raise HTTPException(status_code=400, detail=f"No indices found for for_all='{for_all}'")
        for index in indices:
            _add_constraint(solver, variables, meta, parameters, operator_used, left, right, index)
    else:
        _add_constraint(solver, variables, meta, parameters, operator_used, left, right, None)


def _add_constraint(solver, variables, meta, parameters, operator, left, right, index):
    var_name = _expand_token(left, index)
    variable = variables.get(var_name)
    if variable is None:
        raise HTTPException(status_code=400, detail=f"Unknown decision variable '{var_name}'")

    rhs_value = _evaluate_rhs(right, parameters, index)

    if operator == ">=":
        constraint = solver.Constraint(rhs_value, solver.infinity())
    elif operator == "<=":
        constraint = solver.Constraint(-solver.infinity(), rhs_value)
    else:  # ==
        constraint = solver.Constraint(rhs_value, rhs_value)
    constraint.SetCoefficient(variable, 1)


def _apply_constraint_pyomo(model, variables, meta, parameters, constraint):
    expression = constraint.get("expression")
    if not expression:
        return

    operators = [">=", "<=", "=="]
    operator_used = None
    for op in operators:
        if op in expression:
            operator_used = op
            left, right = expression.split(op)
            break
    if not operator_used:
        raise HTTPException(status_code=400, detail=f"Unsupported constraint expression '{expression}'")

    left = left.strip()
    right = right.strip()
    for_all = constraint.get("for_all")

    if for_all:
        indices = _infer_indices(parameters, for_all)
        if not indices:
            raise HTTPException(status_code=400, detail=f"No indices found for for_all='{for_all}'")
        for index in indices:
            _add_constraint_pyomo(model, variables, meta, parameters, operator_used, left, right, index)
    else:
        _add_constraint_pyomo(model, variables, meta, parameters, operator_used, left, right, None)


def _add_constraint_pyomo(model, variables, meta, parameters, operator, left, right, index):
    var_name = _expand_token(left, index)
    variable = variables.get(var_name)
    if variable is None:
        raise HTTPException(status_code=400, detail=f"Unknown decision variable '{var_name}'")

    rhs_value = _evaluate_rhs(right, parameters, index)
    if operator == ">=":
        model.constraints.add(variable >= rhs_value)
    elif operator == "<=":
        model.constraints.add(variable <= rhs_value)
    elif operator == "==":
        model.constraints.add(variable == rhs_value)
    else:  # pragma: no cover
        raise HTTPException(status_code=400, detail=f"Unsupported operator '{operator}'")


def _expand_token(token: str, index: Optional[str]) -> str:
    if "[" in token and "]" in token:
        base = token[: token.index("[")]
        return f"{base}[{index}]" if index is not None else base
    return token


def _evaluate_rhs(token: str, parameters: dict, index: Optional[str]) -> float:
    token = token.strip()
    if "[" in token and "]" in token:
        base = token[: token.index("[")]
        key = index if index is not None else token[token.index("[") + 1 : token.index("]")]
        values = parameters.get(base, {})
        if key not in values:
            raise HTTPException(status_code=400, detail=f"Missing parameter '{base}[{key}]'")
        return float(values[key])

    try:
        return float(token)
    except ValueError:
        param_value = parameters.get(token)
        if isinstance(param_value, (int, float)):
            return float(param_value)
        raise HTTPException(status_code=400, detail=f"Unable to evaluate RHS '{token}'")


def _compute_linear_cost(ops: dict, decisions: Dict[str, float]) -> float:
    holding_cost = ops.get("parameters", {}).get("holding_cost", {})
    cost = 0.0
    for sku, value in decisions.items():
        cost += float(holding_cost.get(sku, 0.0)) * float(value)
    return cost
