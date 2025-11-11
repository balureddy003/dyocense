# Coach V4 — Phase 1 Implementation Notes

Date: 2025-11-11

## Overview

This phase adds observability and feedback to the Coach chat while preserving the minimal, ChatGPT-like UX:

- Streaming metadata now carries tracing flags and optional run URLs.
- Simple tool-event markers describe agent/tool execution start/end and latency.
- Frontend renders a Trace button (when available), feedback controls, and a compact run details block under assistant messages.

## Backend changes (FastAPI gateway)

Files:

- `services/smb_gateway/multi_agent_coach.py`
- `services/smb_gateway/conversational_coach.py`

### Streaming metadata (LangSmith optional)

Each SSE line is still `data: {json}\n\n`. For the final token chunk of a response, metadata can include:

```json
{
  "tracing_enabled": true,
  "project": "coach",
  "run_url": "https://smith.langchain.com/o/<org>/projects/coach/runs/<runId>"
}
```

Notes:

- If you do not use LangSmith, leave these envs unset. The UI will not show a Trace button and continues to work normally.
- `tracing_enabled` is true if `LANGCHAIN_TRACING_V2=true` (env).
- `project` is set from `LANGCHAIN_PROJECT` (env).
- `run_url` is provided if backend can attach it (e.g., set via `LANGCHAIN_RUN_URL` for now). If absent, the frontend hides the Trace button.

### Tool events

Additionally, chunks may include a single `tool_event` object in metadata:

```json
{
  "tool_event": {
    "type": "start|end",
    "name": "agent:data_scientist",
    "ts": "2025-11-11T10:15:00.000Z",
    "latency_ms": 842
  }
}
```

- `start` is emitted when a specialist agent is selected.
- `end` is emitted on the final chunk with aggregated latency.

## Frontend changes (SMB app)

File:

- `apps/smb/src/pages/CoachV3.tsx`

### Message model additions

```ts
interface Message {
  runUrl?: string
  tracingEnabled?: boolean
  toolEvents?: Array<{ type: string; name?: string; ts?: string; latency_ms?: number }>
  feedback?: 'up' | 'down'
}
```

### SSE handling

- Captures `metadata.run_url`, `metadata.tracing_enabled`, and `metadata.tool_event`.
- Appends tool events to `message.toolEvents` during streaming.

### UI rendering (no LangSmith scenario)

- Under the latest assistant message:
  - "Create Plan" and "Tell me more" remain.
  - Trace button only appears when `runUrl` exists (e.g., when LangSmith is configured). No badge is shown otherwise.
  - Thumbs up/down feedback; posts analytics events (`coach_feedback`).
- A compact "Run details" card lists tool events (start/end with latency).

## Configuration

- Using LangSmith is optional. If you do not configure it, the Coach will still provide a Trace button via local run logs.

- To enable LangSmith (optional):
  - `LANGCHAIN_TRACING_V2=true`
  - `LANGCHAIN_API_KEY=...`
  - `LANGCHAIN_PROJECT=coach`
  - Optional: `LANGCHAIN_RUN_URL=...` (until backend surfaces actual run URLs)

- Local run logs (no LangSmith):
  - Streaming endpoint automatically creates a run log and injects `run_url` like `/v1/tenants/{tenantId}/coach/runs/{runId}` in the final chunk.
  - You can list runs at: `GET /v1/tenants/{tenantId}/coach/runs` and fetch a run at: `GET /v1/tenants/{tenantId}/coach/runs/{runId}`.

## Compatibility

- Streaming and non-streaming flows remain backward compatible.
- Frontend gracefully hides Trace button if no `run_url` is present.

## Follow-ups (Phase 2/3)

- Replace `LANGCHAIN_RUN_URL` placeholder with real run URLs returned by backend via LangSmith SDK.
- Add a feedback modal for comments; wire to LangSmith feedback API when available.
- Show tool I/O (inputs/outputs) in an expandable details panel.
- Add model controls popover and LangServe/LangGraph Studio deep-links.
