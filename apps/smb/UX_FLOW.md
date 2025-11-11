# Cross‑Page UX Flow (Dashboard → Goals → Action Plan → Coach → Analytics)

This document summarizes the guided flow we added and how pages hand off to each other.

## Flow stepper

A reusable `FlowStepper` now appears on key pages with a clear sequence and a context‑aware **Next** button:

1. Connect data → `/connectors`
2. Set goals → `/goals`
3. Build action plan → `/planner`
4. Ask your coach → `/coach`
5. Review analytics → `/analytics`

The stepper shows progress and uses simple heuristics on the Dashboard to decide the current step (connectors exist, goals exist, tasks exist → plan). It’s intentionally lightweight and can be wired to back‑end signals later.

## Page hand‑offs

- Dashboard: Detects state (connectors/goals/tasks) and places the stepper at the top. Primary CTAs still adapt to your state.
- Goals: Inline AI wizard replaces the popup. Stepper cues the next action (“Build action plan”).
- Action Plan (Planner): Stepper nudges to talk to Coach. The page already contains a flow guide and copilot prompts.
- Coach: Compact header kept; a narrow stepper strip is shown above to keep orientation. Quick actions already link to Goals, Tasks, Analytics, and Connectors.
- Analytics: Stepper highlights the final step with quick export buttons and tabs.

## Future improvements

- Persist step completion server‑side and drive the stepper based on true milestones (first connector, first goal, first plan, first chat, first export).
- Add toast after creating the first goal that offers a one‑click jump to the Planner.
- Add an Edit Goal form (creates new version snapshot) and a "Generate Plan from this Goal" button on each goal card.
- Mobile: collapse the stepper to a compact breadcrumb on small screens.
