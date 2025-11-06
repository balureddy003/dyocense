# Goal Planner – GenAI-first flow

This document maps the Trip Planner step-by-step UX to a business planning experience for owners/operators (e.g., a restaurant owner who wants to reduce inventory cost by 5% without compromising quality).

## Flow overview

1. State the goal in natural language (chat)
   - Example: "Reduce inventory cost by 5% without impacting quality across EU."
   - The assistant extracts intent and proposes clarifying questions.
2. Clarify scope and horizon (chat)
   - Assistant asks: business unit/store, markets, horizon (e.g., 12 weeks), key KPIs.
   - If data is missing, assistant requests uploads (e.g., supplier_list.csv, inventory_snapshot.csv).
3. Generate plan variants (Analyze)
   - One-click "Analyze" creates A/B/C variants with different objective trade-offs.
4. Review KPIs and summary
   - Baseline vs Projected for cost, revenue, service level, carbon.
   - Plain language summary + actions list.
5. Refine iteratively
   - Quick refinement chips (extend horizon, tweak weights, lock actions).
   - Keep a refinement history and allow variant switching.
6. Save & Run
   - Save versions locally (UI fallback) or via backend when available.
   - Run scenario (disabled until backend endpoints are wired).

## Implementation notes

- Chat-first: `ChatPanel` drives context and triggers analysis once goal and horizon are captured.
- Live plan preview: `PlanPreview` shows itinerary-like actions and a supplier map placeholder.
- KPIs: `BusinessMetrics` shows projected KPI blocks and baseline vs projected table.
- Variants: Simple A/B/C variants are generated client-side in stub mode.
- Versions: `goalPlannerStore` persists snapshots in `localStorage` (latest 20).
- Feature flag: `VITE_GOAL_PLANNER_FORCE_STUB=1` to force client stubs.

## Backend integration (next)

- Replace stubs in `analyzeGoal`/`refineGoal` with real endpoints.
- Add upload endpoints and schema validation for the requested files.
- Add optimization/forecast runners and scenario persistence.
