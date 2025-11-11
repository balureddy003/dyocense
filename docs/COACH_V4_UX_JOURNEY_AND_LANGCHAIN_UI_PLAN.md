# Coach V4 — UX Journey and LangChain UI Integration Plan

Last updated: 2025-11-11

## Objectives

- Make the Coach experience intuitive, discoverable, and fast for SMB owners and operators.
- Unify chat, goals, plans, and diagnostics into a single, coherent journey.
- Leverage LangChain UI ecosystem to accelerate dev workflows, observability, and end-user confidence.

## Principles

- Minimize cognitive load: progressive disclosure; defaults work well without tuning.
- High-signal context: show only what helps the next decision.
- Traceability by design: every important action is inspectable, reproducible, and shareable.
- Don’t trap users: clear exits to Planner, Goals, and Insights.

## Primary User Journeys

### 1) First-time onboarding (new tenant)

- Trigger: First visit or no goals found.
- Steps:
  1. Greet and explain value briefly (1–2 lines).
  2. Offer 3 guided starters: Define a goal, Generate a weekly plan, Explore insights.
  3. If goal created → store as `latestGoalId` and suggest next: break down goal or create plan.
- Success: User sets at least one meaningful goal or generates a first plan.
- Edge cases: No auth token, missing tenantId, backend 5xx → show resilient hints and retry.

### 2) Daily coaching loop (returning user)

- Trigger: Return to chat with goals/tasks present.
- Steps:
  1. Show compact context (Health, top goal, pending tasks) inline in the first assistant message.
  2. Suggest contextual actions (e.g., “Improve Health Score”, “Weekly Action Plan”).
  3. Support freeform asks; classify intent; route via agents.
- Success: A helpful, grounded response; optional plan creation.
- Edge cases: Streaming down, tool error; show graceful fallback and telemetry.

### 3) Goal breakdown → plan generation

- Trigger: User requests breakdown or plan.
- Steps:
  1. Use goal context; propose steps with owners/due dates.
  2. "Create Plan" quick action posts `/v1/tenants/:id/plans` with `goal_id`.
- Success: Plan created and visible in Planner; link back to Coach with breadcrumbs.

### 4) Insights/Diagnostics (explain why)

- Trigger: User asks "why?" or requests prediction.
- Steps:
  1. Show explanation with any cited sources (RAG) and charts where possible.
  2. Allow “Open Trace” to inspect the run.
- Success: User understands rationale and next steps.

### 5) Multi-agent branching (advisor switching)

- Trigger: Change persona mid-thread.
- Steps:
  1. Clearly display advisor context; preserve history but indicate persona switch.
  2. Tool runs show agent attribution.
- Success: User sees continuity and reason for agent choice.

## Information Architecture (IA)

- Left Sidebar (persistent; collapsible)
  - Chat search
  - Conversations (recent, pinned)
  - Active Goals (quick switch)
  - Files/Datasets (for RAG) [future]
  - Agents (shortcuts) [future]

- Header
  - Title, subtle tagline
  - Quick nav to Goals and Planner
  - Model settings (collapsed) [future]

- Chat Thread (center)
  - Messages (user, assistant)
  - Inline context summary under first assistant message
  - Tool call/stream blocks with status and details
  - Inline actions (Create Plan, Tell me more)

- Composer (bottom)
  - Textarea, send
  - Attach files (docs, CSV) [future]
  - Variables panel (goal, date range, dataset) [future]

- Inspector (right drawer or link-out)
  - Run trace, tool inputs/outputs
  - Parameters (model, temperature)
  - Feedback (👍/👎 with comment)

## Component → Backend/API mapping

- Goals summary (sidebar/inline) → `GET /v1/tenants/{tenantId}/goals`
- Health, tasks (inline) → `GET /v1/tenants/{tenantId}/health-score`, `GET /v1/tenants/{tenantId}/tasks?status=todo`
- Chat (SSE + fallback) → `POST /v1/tenants/{tenantId}/coach/chat/stream` and `POST /v1/tenants/{tenantId}/coach/chat`
- Plan creation → `POST /v1/tenants/{tenantId}/plans` with `{ goal_id }`
- Telemetry → `POST /v1/analytics/events`

## LangChain UI capabilities to leverage

- LangSmith Tracing & Feedback
  - Enable via env:
    - `LANGCHAIN_TRACING_V2=true`
    - `LANGCHAIN_API_KEY=<key>`
    - Optional: `LANGCHAIN_PROJECT=coach`
  - Capture traces for each chat turn and tool call.
  - Add per-message feedback (👍/👎 + comment) and send to LangSmith.
  - “Open Trace” button: deep-link to LangSmith run URL.

- LangServe Playground (per endpoint)
  - Expose runnable endpoints behind FastAPI using LangServe.
  - Provide “Open in Playground” from UI for advanced users.

- LangGraph Studio (graph dev + inspection)
  - Maintain graph-based agents in the backend; provide “Open in Studio” link for developers.
  - Supports node-level replay and branch comparisons.

- Callbacks/Streaming
  - Use `with_config` and callback handlers to stream tokens and tool events.
  - Visualize tool events in chat (pending → running → done; show inputs/outputs optionally).

- Datasets/Evals [future]
  - Collect anonymized (or consented) runs into datasets; evaluate prompts/agents over time.
  - Use LangSmith datasets for regression testing before releases.

## Rich features backlog (prioritized)

1. Inspectability
   - Trace button on each assistant message (open LangSmith run)
   - Tool call disclosure with expandable IO

2. Source citations & doc viewer (RAG)
   - Inline citations with hover preview
   - Right panel to view source passages

3. Model & Agent controls (collapsed by default)
   - Model selector, temperature, max tokens
   - Persona/agent dropdown with descriptions

4. Saved prompts & templates
   - Quick picks for common tasks
   - User-defined templates

5. Compare runs
   - Select two assistant messages to diff content and latency

6. Dataset-based evals (internal only)
   - “Evaluate this prompt” against a curated dataset; open results in LangSmith

## Incremental implementation plan

Phase 1 (Ship-ready)

- Polished chat layout with sidebar search and inline context (done baseline).
- Add “Trace” button on assistant messages when `LANGCHAIN_TRACING_V2` active.
- Add feedback (👍/👎) storing to LangSmith if configured; else to analytics.
- Surface tool calls in-stream (status + small details panel).

Phase 2 (Power-user features)

- Model settings popover (model, temperature, top_p).
- “Open in Playground” (LangServe) and “Open in Studio” links (dev mode).
- Source citations with hover preview (if RAG enabled in backend).

Phase 3 (Quality & scale)

- Saved prompts/templates and parameter presets.
- Compare runs UI and basic dataset eval trigger.
- Accessibility polish; keyboard nav; screen-reader labels.

## Telemetry and success metrics

- KPIs:
  - Time-to-first-plan, reply latency (P50/P95), error rate.
  - Feature engagement: Trace opens, feedback submissions, Playground/Studio usage.
  - Session retention: 7-day and 30-day return rate to Coach.
- Events:
  - `coach_chat_sent`, `coach_chat_failed`, `plan_creation_success/failed`, `trace_opened`, `feedback_submitted`, `playground_opened`, `studio_opened`.

## Edge cases and error UX

- Streaming fails: switch to non-streaming POST and inform subtly.
- Tool error: display friendly error block with retry + details toggle.
- No goals/tasks: show clear CTA to create goals and generate a plan.
- Auth/tenant missing: redirect to sign-in or tenant picker.

## Technical integration notes

- Backend
  - Wrap chat pipeline as a Runnable with callbacks for streaming and tool events.
  - Configure LangSmith tracing (guard by envs) and attach run URLs to responses for UI.
  - Optional: serve via LangServe for built-in Playground.

- Frontend
  - Add optional Trace button on assistant messages when `run_url` available.
  - Add feedback controls; post to LangSmith if keys present, else to `/v1/analytics/events`.
  - Visualize tool events inline with compact expandable blocks.

## Acceptance criteria (Phase 1)

- Users can discover context with minimal clutter.
- Each assistant response (when tracing on) has a working Trace link.
- Feedback works and is recorded to LangSmith or analytics.
- Tool runs visible and don’t overwhelm the thread.

## Try it (optional env setup)

```bash
# Backend (FastAPI) with LangSmith tracing enabled
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=... # required for tracing
export LANGCHAIN_PROJECT=coach

# Start gateway and kernel (examples)
python -m uvicorn services.smb_gateway.main:app --reload --host 127.0.0.1 --port 8000
python -m uvicorn services.kernel.main:app --reload --host 127.0.0.1 --port 8001

# Frontend
cd apps/smb
npm run dev
```
