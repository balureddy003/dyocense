# Evidence Graph — DESIGN (Detailed)

Stores provenance for every plan decision: *what data, constraints, and trade‑offs produced which steps*. Implemented in **Neo4j** with snapshots (JSON + hash) in **MinIO**.

---

## 1) Node & Edge Schema
- **Nodes**: `Goal`, `Question`, `DataSource`, `Feature`, `Constraint`, `Objective`, `Scenario`, `SolverRun`, `Plan`, `Step`, `KPI`.
- **Edges**: `DERIVED_FROM`, `CONSTRAINS`, `OPTIMIZES`, `SUPPORTS`, `MEASURED_BY`, `EXECUTED_AS`.

```mermaid
classDiagram
  class Goal{ id text goal_dsl created_at }
  class Question{ id field value voi_score }
  class DataSource{ id uri hash ts }
  class Feature{ id name value source }
  class Constraint{ id name active dual sensitivity }
  class Objective{ id name weight }
  class Scenario{ id idx demand_lt }
  class SolverRun{ id status gap time_limit }
  class Plan{ id variant total_cost service co2 }
  class Step{ id sku supplier qty price due_date }
  class KPI{ id name value period }
  Goal --> Question
  Goal --> Plan
  Plan --> Step
  Plan --> KPI
  SolverRun --> Plan
  Constraint --> SolverRun
  Objective --> SolverRun
  DataSource --> Feature
```

## 2) Write Flow
```mermaid
flowchart LR
  A[Optimizer Output + Hints] --> B(Build Graph batch)
  B --> C(Upsert Nodes)
  C --> D(Upsert Edges)
  D --> E(Snapshot JSON to MinIO + hash)
  E --> F(Return EvidenceRef)
```

## 3) Sequence (after solve)
```mermaid
sequenceDiagram
  participant OP as Optimizer
  participant EG as Evidence
  OP->>EG: POST /evidence {plan_id, constraints, duals, steps, kpis}
  EG->>EG: upsert nodes/edges
  EG->>EG: write snapshot to MinIO
  EG-->>OP: evidence_ref
```

## 4) Query Patterns
- “Why vendor X?” → follow `Step -> DERIVED_FROM (Constraint, Objective, Data)`
- “Which constraints bound?” → filter `Constraint.active=true` on `SolverRun`

## 5) Retention & Privacy
- Hash PII in snapshots; redact logs; TTL for raw artifacts; keep graph structure for audit.
