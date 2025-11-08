# Agent-Driven Data Upload & Connect Flow - Implementation Summary

## Overview

Transformed the AI Business Assistant from a hardcoded, rule-based UI into a fully agent-driven conversational experience for data upload and connect operations.

## Key Changes

### 1. Agent-Driven System Prompt

- Added `AGENT_SYSTEM_PROMPT` that guides the LLM to:
  - Hold natural conversations about business planning
  - Acknowledge file uploads and infer schema
  - Suggest connectors based on user context
  - Ask clarifying questions only when needed
  - Provide concise, actionable next steps

### 2. Feature Flag for Agent Mode

- `AGENT_DRIVEN_FLOW = true` enables fully LLM-guided conversations
- Disables legacy hardcoded Q&A flows and SMART goal questions
- Can be toggled back to structured mode if needed

### 3. File Upload Flow

#### Before (Hardcoded)

```typescript
// Static response after upload
setMessages("File uploaded! Would you like to connect or preview?")
```

#### After (Agent-Driven)

```typescript
// Process file, parse data, call LLM with full context
const processedSource = await processFileUpload(file);
const oaiResp = await postOpenAIChat({
  messages: [
    { role: "system", content: AGENT_SYSTEM_PROMPT },
    ...chatHistory,
    { role: "user", content: `Uploaded ${file.name} with ${rows} rows, columns: ${cols}` }
  ],
  context: {
    uploaded_file: { name, size, rows, columns },
    data_sources: [...existing],
    connectors: [...active],
    tenant_id, preferences
  }
});
// Display agent's dynamic response with action buttons
```

### 4. Real File Processing

- `processFileUpload()` function:
  - Reads and parses CSV/JSON files
  - Extracts schema (columns) and preview data
  - Persists to localStorage and state
  - Returns typed `DataSource` object

### 5. Action Buttons in Chat

Messages now support action buttons:

```typescript
{
  role: "assistant",
  text: "File uploaded with 150 rows!",
  actions: [
    { label: "Preview Data", action: "preview", data: { sourceId } },
    { label: "Analyze", action: "analyze", data: { sourceId } },
    { label: "Remove", action: "remove", data: { sourceId } }
  ]
}
```

### 6. Data Operations with Agent Feedback

#### Preview Data

- Shows first 5 rows in chat as formatted table
- Agent can reference this in follow-up responses

#### Remove Data Source

- Removes from state and localStorage
- Calls agent to acknowledge and suggest next steps

#### Connect Data Source

- After connection completes, agent summarizes what's now possible
- No more hardcoded "✓ Connected successfully" messages

### 7. Intent Parsing

Basic intent parsing for common commands:

- "preview restaurant_inventory.csv" → triggers preview
- "remove sales_data.json" → triggers removal
- Falls back to agent for complex queries

### 8. Connector Setup Completion

When a connector is configured:

```typescript
// Before: static message
setMessages("✓ Shopify connected!")

// After: agent summarizes capabilities
const resp = await postOpenAIChat({
  messages: [...history, { role: "user", content: "Shopify connector is now connected" }],
  context: { connectors: updatedList }
});
```

### 9. Rich Context in Every LLM Call

Every agent call includes:

- System prompt with assistant persona
- Full chat history
- Current data sources (name, rows, columns, type)
- Active connectors (name, type, status)
- Tenant ID and preferences
- Specific action context (file uploaded, connector added, etc.)

## User Experience Improvements

### ChatGPT-like Flow

1. User uploads file via chat input "Upload" button
2. File is processed and parsed automatically
3. Agent responds with personalized next steps based on file content
4. Action buttons appear for common operations (preview, analyze, remove)
5. User can click buttons OR type natural language commands
6. Agent maintains context across all interactions

### No More

- ❌ "Would you like to connect or preview?" (hardcoded)
- ❌ Predefined SMART goal questions
- ❌ Static confirmation messages
- ❌ Separate modes for data vs. chat

### Now

- ✅ Dynamic agent responses based on actual data
- ✅ Inline action buttons in chat
- ✅ Natural language commands ("preview sales data")
- ✅ Context-aware suggestions
- ✅ Unified conversational interface

## API Integration Points

### Required Backend Endpoints

1. `/v1/chat/completions` - OpenAI-compatible chat endpoint
   - Receives system prompt, chat history, context
   - Returns agent's natural language response

2. `/v1/connectors` (already implemented)
   - List, create, test connectors
   - Used after connector setup completes

3. Future: `/v1/files/upload` (optional)
   - For server-side file storage
   - Currently using localStorage + client-side parsing

## Testing

### Build Status

✅ Successfully builds without errors

```bash
cd apps/ui
npm run build
# ✓ built in 1.37s
```

### Manual Test Steps

1. **Upload a CSV file**:
   - Click "Upload" button in chat input
   - Select restaurant_inventory.csv
   - Verify: Agent responds with row count, column names, and action buttons

2. **Preview data**:
   - Click "Preview Data" button OR type "preview restaurant_inventory.csv"
   - Verify: First 5 rows appear in chat as formatted text

3. **Connect a connector**:
   - Click "Connectors" tab or mention "POS system" in chat
   - Complete setup for Square/Shopify
   - Verify: Agent acknowledges with capabilities summary

4. **Remove data source**:
   - Click "Remove" button OR type "remove restaurant_inventory.csv"
   - Verify: Agent confirms removal and suggests alternatives

5. **Analyze data**:
   - Click "Analyze" button
   - Verify: Input field auto-fills with "Analyze the data in [filename]"
   - Send message
   - Verify: Agent provides analysis recommendations

## Configuration

### Enable/Disable Agent Mode

```typescript
// In AgentAssistant.tsx
const AGENT_DRIVEN_FLOW = true;  // Set to false for legacy mode
```

### Customize System Prompt

```typescript
const AGENT_SYSTEM_PROMPT = `You are Dyocense's AI Business Assistant.
- [Your custom instructions here]
`;
```

## Next Steps (Optional Enhancements)

1. **Streaming Responses**
   - Enable `stream: true` in chat API calls
   - Show typing indicator and incremental text

2. **Tool Calling**
   - Use function calling for structured actions
   - Let agent explicitly invoke preview/remove/connect

3. **Backend File Storage**
   - POST files to `/v1/files/upload`
   - Store file metadata and references in database

4. **Data Visualization**
   - Render preview data as interactive tables
   - Show charts for numeric columns

5. **Multi-turn Analysis**
   - Agent can request specific data operations
   - "Show me rows where revenue > $1000"
   - Execute queries and display results in chat

## Files Modified

- `apps/ui/src/components/AgentAssistant.tsx` (main implementation)
  - Added agent system prompt and feature flag
  - Implemented `processFileUpload()` for real parsing
  - Added `handleDataSourcePreview()`, `handleDataSourceRemove()`
  - Enhanced file upload onChange handler
  - Updated connector setup completion
  - Added action button rendering and handling
  - Integrated intent parsing in `handleSend()`

## Summary

The AI Business Assistant now operates as a true conversational agent, where every user action (upload, connect, remove) triggers an LLM call with rich context, and the agent responds dynamically based on the actual state of data sources and connectors. Hardcoded flows have been replaced with natural language interactions backed by real data processing.
