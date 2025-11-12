# LangGraph-Based Coach Workflow

## Overview

Replaced custom task planner orchestration with native LangGraph capabilities for cleaner, more maintainable code.

## Architecture

### State Schema (`CoachState`)

```python
class CoachState(TypedDict):
    # Input
    tenant_id: str
    user_message: str
    conversation_history: List[BaseMessage]
    
    # Business context
    business_context: Dict[str, Any]
    available_data: Dict[str, List[Dict[str, Any]]]
    
    # Workflow tracking
    intent: Optional[str]
    sub_tasks: List[Dict[str, Any]]
    completed_tasks: List[Dict[str, Any]]
    current_task_index: int
    
    # Results
    task_results: Dict[str, Any]
    report_id: Optional[str]
    final_response: str
    
    # Human-in-the-loop
    pending_approval: Optional[Dict[str, Any]]
    human_feedback: Optional[str]
```

### Workflow Nodes

1. **analyze_intent**: Detect user intent and plan sub-tasks
2. **execute_task**: Run current sub-task
3. **check_approval**: Check if task needs human approval (HITL gate)
4. **apply_feedback**: Apply human corrections after approval
5. **generate_report**: Create downloadable report
6. **generate_analysis**: Final AI analysis with LLM

### Key Features

- **Native HITL**: Uses LangGraph's `interrupt_before` instead of custom PENDING_EXECUTIONS
- **Conditional Approval**: Only requires human approval when tasks explicitly need it (based on `requires_approval` flag)
- **Checkpointing**: Automatic state persistence with thread_id
- **Streaming**: LangGraph's `.astream()` replaces custom SSE logic
- **Resume**: `update_state()` to continue after approval

### Conditional Approval

Tasks can optionally require human approval:

```python
sub_tasks.append({
    "id": "generate_report",
    "description": "📝 Generating detailed report",
    "status": "pending",
    "requires_approval": True  # This task will pause for human review
})
```

By default, most tasks execute automatically. Approval is only required when:

- Task explicitly has `requires_approval: True`
- User requests "detailed report" or "comprehensive analysis"

This reduces interruptions for simple queries while maintaining oversight for critical actions.

## API Endpoints

### Stream Chat (LangGraph)

```
POST /v1/tenants/{tenant_id}/coach/chat/stream/v2
```

**Request:**

```json
{
  "message": "Analyze my inventory",
  "conversation_history": [],
  "persona": "business_analyst"
}
```

**Response:** SSE stream with chunks matching frontend format

### Resume After Approval

```
GET /v1/tenants/{tenant_id}/coach/chat/resume-langgraph/{thread_id}/stream
```

Uses LangGraph's `update_state()` to continue execution.

## Migration Path

### Phase 1: Parallel Deployment (Current)

- New endpoint: `/coach/chat/stream/v2`
- Old endpoint: `/coach/chat/stream` (legacy)
- Frontend can switch via config flag

### Phase 2: Frontend Switch

- Update `CoachV4.tsx` to use `/v2` endpoint
- Test HITL flow with LangGraph checkpoints

### Phase 3: Deprecate Legacy

- Remove custom `task_planner.py`
- Remove `PENDING_EXECUTIONS` in-memory store
- Keep `/v1` as fallback for 1 release

## Benefits vs Custom Implementation

| Feature | Custom | LangGraph |
|---------|--------|-----------|
| State Management | Manual dict tracking | Typed TypedDict schema |
| HITL | In-memory PENDING_EXECUTIONS | Native interrupt_before |
| Resume | Custom endpoint + context restore | update_state() one-liner |
| Persistence | In-memory or custom DB | Built-in checkpointers |
| Streaming | Manual SSE formatting | Native .astream() |
| Debugging | Custom logging | LangSmith integration |
| Testing | Custom mocks | LangGraph test harness |

## Configuration

### Checkpointer (Persistence)

**Memory (default):**

```python
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
```

**PostgreSQL (production):**

```bash
export POSTGRES_URL="postgresql://user:pass@host:5432/db"
```

```python
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string(os.getenv("POSTGRES_URL"))
```

### Tracing (optional)

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_PROJECT="dyocense-coach"
export LANGCHAIN_API_KEY="<your-key>"
```

## Frontend Integration

### Current Custom Approach

```typescript
const response = await fetch(`/v1/tenants/${tenantId}/coach/chat/stream`, {
  method: 'POST',
  body: JSON.stringify({ message, conversation_history })
})
```

### New LangGraph Approach

```typescript
const response = await fetch(`/v1/tenants/${tenantId}/coach/chat/stream/v2`, {
  method: 'POST',
  body: JSON.stringify({ message, conversation_history })
})

// Response headers include thread_id for resume
const threadId = response.headers.get('X-Thread-ID')
```

### Resume After Approval

```typescript
// After approval:
const resumeResponse = await fetch(
  `/v1/tenants/${tenantId}/coach/chat/resume-langgraph/${threadId}/stream`
)
```

## Files

- `services/smb_gateway/coach_langgraph_workflow.py` - LangGraph state + nodes
- `services/smb_gateway/coach_langgraph_streaming.py` - SSE adapter
- `services/smb_gateway/coach_langgraph_resume.py` - HITL resume handler
- `services/smb_gateway/main.py` - `/v2` endpoint

## Next Steps

1. **Test v2 endpoint** with existing UI
2. **Switch frontend** to use v2 by default
3. **Monitor** for any regressions
4. **Remove legacy** after 1 release cycle
5. **Add PostgreSQL checkpointer** for cross-device sync

## Rollback Plan

If issues arise:

1. Switch frontend back to `/coach/chat/stream` (no v2)
2. Legacy implementation remains unchanged
3. No data loss (frontend uses localStorage)
