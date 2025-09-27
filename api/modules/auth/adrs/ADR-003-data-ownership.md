# ADR-003: Data Ownership — auth Service
## Decision
Own tables: tenant, user, role_assignment. Emit domain events via Redis for projections.
