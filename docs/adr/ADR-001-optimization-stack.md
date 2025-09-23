# ADR-001: Optimization Stack
## Status
Accepted
## Context
SMB procurement MILPs require fast solves and explainability.
## Decision
Use OptiGuide (GoalDSL→MILP) atop OR‑Tools CP‑SAT. Use Pyomo where needed.
## Consequences
- Performance + rich modeling.
- Maintain a stable GoalDSL → model compiler interface.
