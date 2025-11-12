# LangGraph Migration - Cleaner Coach Workflow

## What Changed

Replaced custom task planner with native LangGraph for:

- ✅ **Cleaner state management** with TypedDict
- ✅ **Native HITL** using `interrupt_before`
- ✅ **Conditional approval** - only pauses when tasks truly need it
- ✅ **Built-in checkpointing** (no manual PENDING_EXECUTIONS)
- ✅ **Standard streaming** via `.astream()`
- ✅ **One-line resume** with `update_state()`
- ✅ **LangSmith tracing** support

## Quick Start

### Backend (v2 endpoint already live)

```python
# New endpoint (cleaner):
POST /v1/tenants/{tenant_id}/coach/chat/stream/v2

# Same request format as v1
{
  "message": "Analyze my inventory",
  "persona": "business_analyst"
}
```

### Frontend Switch

To use the new cleaner flow, change one line in `CoachV4.tsx`:

```typescript
// OLD (custom):
const response = await fetch(`${API_BASE}/v1/tenants/${tenantId}/coach/chat/stream`, ...)

// NEW (LangGraph):
const response = await fetch(`${API_BASE}/v1/tenants/${tenantId}/coach/chat/stream/v2`, ...)
```

That's it! The SSE format is identical, so no other changes needed.

## What's Better

| Aspect | Before (Custom) | After (LangGraph) |
|--------|----------------|-------------------|
| **Code** | 500+ lines custom orchestration | 300 lines using LangGraph primitives |
| **HITL** | Manual `PENDING_EXECUTIONS` dict | Native `interrupt_before` |
| **Approval** | Always required for reports | Conditional based on task requirements |
| **Resume** | Custom endpoint + state restore | `update_state()` built-in |
| **Persistence** | In-memory only | Pluggable checkpointers (Memory/Postgres) |
| **Testing** | Custom mocks | LangGraph test harness |
| **Debugging** | Manual logs | LangSmith visual tracing |

## Files Created

- `services/smb_gateway/coach_langgraph_workflow.py` - State + graph nodes
- `services/smb_gateway/coach_langgraph_streaming.py` - SSE adapter
- `services/smb_gateway/coach_langgraph_resume.py` - HITL resume
- `LANGGRAPH_MIGRATION.md` - Full migration guide

## Try It

1. Test v2 endpoint in browser (already deployed)
2. Verify HITL approval flow works
3. Switch frontend to `/v2` when ready

## Rollback

Legacy `/v1` endpoint unchanged - switch back anytime.
