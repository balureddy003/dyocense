# Goal Planner – Concept Mapping from Trip AI Planner

This document maps the Trip.com “Trip AI Planner” UX concepts to Dyocense’s business planning flows (goals → compiled plan → optimise → refine → save).

Last updated: 2025-11-05

---

## UX concept mapping

Trip.com → Dyocense

- Starting from (origin city) → Business context (business unit, market, product line)
- Heading to (destinations) → Target outcomes (KPIs to hit; markets to expand; SKUs to prioritise)
- Date/Duration → Planning horizon (weeks/months) or specific calendar window
- Preferences modal → Strategy toggles & policy constraints (cost focus, growth focus, service-level target, ESG rules)
- Plan a Trip with AI → Compile + Optimise plan (compiler → optimiser → scenario)
- Create It Myself → Manual scenario setup (seed plan with defaults; user edits)
- My Itineraries → My Plans / Scenarios (saved runs per tenant/project)
- Refine via chat → PlanDelta (adjust horizon, shift objective weights, add/remove constraints, lock actions)

---

## State machine

1. Start → collect minimal inputs
2. InputsReady → user has business unit/goal/horizon
3. Planning → call compile (OPS) and optimise
4. PlanReady → render KPIs, actions, schedule
5. Refining ↔ apply PlanDelta and re-run
6. Saved → persist plan & version
7. Execution/Booking → optional deep links (e.g., procurement tasks)

Error modes: validation errors, infeasible constraints (diagnostician), timeouts.

---

## Contracts (high level)

Inputs (GoalRequest)

- tenant_id, project_id
- business_context: { business_unit_id, markets[], products[] }
- goal_text: free-text description of the business objective
- horizon: { unit: "weeks|months", value: integer } or { start_date, end_date }
- objectives: { cost_minimise?, revenue_maximise?, service_level_target?, carbon_cap? } with weights
- policies: identifiers of policy bundles (e.g., compliance/sustainability)
- constraints: [{ name, type, value }]
- data_inputs?: dataset references (inventory, demand, capacity)

Outputs (GoalPlan)

- id, version, summary
- kpis: { baseline, projected }
- actions: [{ id, type, entity, delta, rationale }]
- schedule: time-bucketed actions
- risks: [text]
- assumptions: [text]

Refinements (PlanDelta)

- adjust_horizon, change_objective_weights, add/remove constraint, relax constraint, lock_actions[], scenario_tags[]

Detailed JSON Schema lives in `docs/schemas/goal_planner.schema.json`.

---

## API surface (OpenAPI stub)

- POST /v1/goal-planner/analyze → GoalRequest → GoalPlan (initial plan)
- POST /v1/goal-plans/{id}/refine → PlanDelta → GoalPlan
- GET /v1/goal-plans/{id}
- POST /v1/goal-plans/{id}/save
- POST /v1/goal-plans/{id}/run → triggers full orchestrator

OpenAPI spec is in `docs/openapi/goal_planner.yaml`.

---

## UI mapping

- Header inputs mirror Trip layout:
  - BusinessContextPicker (unit, markets)
  - TargetKPIChips (e.g., 95% service level, ≤ x% cost increase)
  - HorizonPicker (weeks/months or date range)
  - PreferencesModal (strategy focus & policy toggles)
  - CTAs: Create scenario, Plan with AI
- Plan view: KPI deltas vs baseline; actions timeline; map/table widgets as relevant
- Refine: deterministic chat → produces PlanDelta; “Apply” chip; re-run

---

## Acceptance criteria

- Minimal inputs produce a deterministic initial plan (stub OK)
- Preferences affect plan (e.g., cost vs service-level tilt)
- Refinements are idempotent PlanDeltas with visible KPI deltas
- Saved plans include version history and assumptions

---

## Next steps

- Scaffold UI page "GoalPlanner" in `apps/ui` using the above inputs
- Implement stub endpoints from the OpenAPI spec and route through Kernel
- Reuse deterministic chat PlanDelta logic introduced for Playbook results
