from __future__ import annotations

from copy import deepcopy

import pytest

from services.optimiser import main as optimiser


def _base_ops():
    return {
        "metadata": {"ops_version": "1.0.0", "project_id": "test", "archetype_id": "inventory"},
        "parameters": {"demand": {"widget": 10}, "holding_cost": {"widget": 1.0}},
        "decision_variables": [{"name": "stock", "type": "integer", "lb": 0, "index_sets": ["demand"]}],
        "constraints": [{"name": "demand", "for_all": "demand", "expression": "stock[demand] >= demand[demand]"}],
        "objective": {"sense": "min"},
    }


def test_pyomo_backend_dispatch(monkeypatch):
    monkeypatch.setenv("OPTIMISER_BACKEND", "pyomo")
    monkeypatch.setattr(optimiser, "HAS_PYOMO", True)

    def fake_pyomo(ops, warm_start=None):
        return optimiser._construct_solution(
            ops,
            solver_name="pyomo-test",
            decisions={"stock": {"widget": 10.0}},
            objective_value=10.0,
            status_text="optimal",
            notes=["unit-test"],
        )

    monkeypatch.setattr(optimiser, "_solve_with_pyomo", fake_pyomo)
    result = optimiser.optimise_ops_document(deepcopy(_base_ops()))
    assert result["metadata"]["solver"] == "pyomo-test"
    monkeypatch.delenv("OPTIMISER_BACKEND", raising=False)


def test_pyomo_backend_falls_back_to_ortools(monkeypatch):
    monkeypatch.setenv("OPTIMISER_BACKEND", "pyomo")
    monkeypatch.setattr(optimiser, "HAS_PYOMO", False)
    monkeypatch.setattr(optimiser, "HAS_SOLVER", True)

    call_flag = {}

    def fake_ortools(ops, warm_start=None):
        call_flag["called"] = True
        return optimiser._construct_solution(
            ops,
            solver_name="cbc-test",
            decisions={"stock": {"widget": 10.0}},
            objective_value=10.0,
            status_text="optimal",
            notes=["ortools-fallback"],
        )

    monkeypatch.setattr(optimiser, "_solve_with_ortools", fake_ortools)
    result = optimiser.optimise_ops_document(deepcopy(_base_ops()))
    assert result["metadata"]["solver"] == "cbc-test"
    assert call_flag.get("called")
    monkeypatch.delenv("OPTIMISER_BACKEND", raising=False)


def test_stub_used_when_no_solvers(monkeypatch):
    monkeypatch.delenv("OPTIMISER_BACKEND", raising=False)
    monkeypatch.setattr(optimiser, "HAS_SOLVER", False)
    monkeypatch.setattr(optimiser, "HAS_PYOMO", False)
    result = optimiser.optimise_ops_document(deepcopy(_base_ops()))
    assert result["metadata"]["solver"] == "stub-optimiser"


def test_warm_start_annotation(monkeypatch):
    ops = _base_ops()
    monkeypatch.setattr(optimiser, "HAS_SOLVER", False)
    monkeypatch.setattr(optimiser, "HAS_PYOMO", False)
    warm_start = {"decisions": {"stock": {"widget": 12}}}

    solution = optimiser.optimise_ops_document(deepcopy(ops), warm_start=warm_start)
    diagnostics = solution["diagnostics"]
    assert "warm_start" in diagnostics
    warm_info = diagnostics["warm_start"]
    assert warm_info["objective_warm_start"] is not None
