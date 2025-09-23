# ADR-003: Data Ownership — scheduler Service
## Decision
Own tables: job_run, job_metric. Emit domain events via Redis for projections.
