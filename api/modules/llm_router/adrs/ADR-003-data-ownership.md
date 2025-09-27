# ADR-003: Data Ownership — llm-router Service
## Decision
Own tables: model_budget, route_policy, llm_metric. Emit domain events via Redis for projections.
