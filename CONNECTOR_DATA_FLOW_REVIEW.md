# Connector & Data Upload Flow Review

## Current State Analysis

### Problem: Disjointed User Experience

The current implementation has **two major UX issues**:

1. **Connectors and data upload appear as separate modal windows** that interrupt the conversation flow
2. **They feel disconnected from the AI assistant** - like switching to a different app rather than a guided experience
3. **No conversational guidance** - users just see forms/UI without the agent explaining what's happening

### Current Implementation

#### 1. Connector Flow (Lines 2206-2229)

```tsx
{showConnectorMarketplace && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh]">
      <ConnectorMarketplace
        onConnectorSelected={handleConnectorSelected}
        tenantId={profile?.tenant_id || ""}
      />
    </div>
  </div>
)}
```

**Issues:**

- ❌ Pops up as full-screen modal overlay - breaks conversation context
- ❌ No agent explanation of why connectors are being shown
- ❌ Silent trigger via `suggestConnectorFromIntent()` - user doesn't know why it happened
- ❌ Forces user out of chat experience

#### 2. Data Upload Flow (Lines 1940-1946)

```tsx
{mode === "data-upload" && (
  <div>
    <h3 className="mb-4 text-lg font-bold">Upload Data & Connect Sources</h3>
    <DataUploader onDataSourceAdded={handleDataSourceAdded} existingSources={dataSources} />
  </div>
)}
```

**Issues:**

- ❌ Replaces entire chat interface with upload form
- ❌ Mode switching (`mode === "data-upload"`) hides the conversation
- ❌ No agent guidance during the upload process
- ❌ After upload completes, there's a message but no smooth transition back

#### 3. Connector Intent Detection (Lines 1499-1503)

```tsx
const connectorIntent = suggestConnectorFromIntent(userInput);
if (connectorIntent && profile?.tenant_id) {
  setShowConnectorMarketplace(true);
  setMode("connectors");
}
```

**Issues:**

- ❌ Keyword-based detection (not LLM-driven)
- ❌ Silently opens marketplace without asking user
- ❌ No agent message explaining the transition
- ❌ Disrupts conversation flow

---

## Proposed Solution: LLM-Driven Inline Flow

### Philosophy: Keep Everything Conversational

Instead of modals and mode switches, the agent should:

1. **Explain what's needed** ("To help with sales forecasting, let's connect your CRM data")
2. **Guide the user through options** (show connector cards inline in chat)
3. **Provide real-time feedback** ("Great! Configuring Salesforce connector...")
4. **Summarize and continue** ("✓ Connected. I can see 500 leads. Ready to analyze?")

---

## Implementation Plan

### Phase 1: Replace Connector Modal with Inline Cards

**Current:** Full-screen modal that blocks everything
**New:** Inline connector cards in the chat stream

```tsx
// Instead of modal, agent sends a message with embedded connector options:
{
  id: "msg-123",
  role: "assistant",
  text: "I can help you connect these data sources:",
  embeddedComponent: "connector-selector",
  componentData: {
    suggestedConnectors: ["salesforce", "stripe", "shopify"],
    context: "sales_analysis"
  }
}
```

**Implementation:**

1. Add `embeddedComponent` field to `Message` type
2. Create `<InlineConnectorSelector>` component that renders in chat
3. Update `handleSend()` to let LLM decide when to suggest connectors
4. Remove `showConnectorMarketplace` modal state

---

### Phase 2: Replace Data Upload Mode with Inline Uploader

**Current:** Mode switch that replaces chat interface
**New:** Inline upload widget that appears in chat

```tsx
// Agent message with embedded uploader:
{
  id: "msg-124",
  role: "assistant",
  text: "Upload your CSV file here, and I'll analyze it:",
  embeddedComponent: "data-uploader",
  componentData: {
    acceptedFormats: [".csv", ".xlsx"],
    expectedColumns: ["date", "sales", "region"]
  }
}
```

**Implementation:**

1. Create `<InlineDataUploader>` component (compact, chat-friendly)
2. Add upload progress inline in message
3. Update `handleDataSourceAdded()` to show agent's reaction
4. Remove `mode === "data-upload"` switching logic

---

### Phase 3: LLM-Driven Flow Control

**Current:** Hardcoded `suggestConnectorFromIntent()` keyword matching
**New:** LLM decides when to offer connectors/uploads

```tsx
// Enhanced system prompt:
"When users need data to accomplish their goal:
1. Explain why data is needed
2. Suggest specific data sources (connectors or upload)
3. Use function calling to trigger inline UI:
   - show_connector_options(connectors: string[])
   - show_data_uploader(format: string)
4. Guide users through setup with encouraging messages"
```

**Implementation:**

1. Add function calling schema to LLM prompts
2. Parse LLM function calls in response
3. Render appropriate inline components
4. Remove hardcoded `suggestConnectorFromIntent()` logic

---

### Phase 4: Conversational Setup Guidance

**Current:** `ChatConnectorSetup` appears as separate modal
**New:** Agent guides through setup in conversation

```tsx
// Multi-turn setup conversation:
Agent: "Let's connect Salesforce. I need a few details:"
Agent: "1. Enter your Salesforce instance URL" [inline input field]
User: "https://mycompany.salesforce.com"
Agent: "Got it! 2. Provide your API key" [secure inline input]
User: [enters key]
Agent: "✓ Testing connection..." [inline spinner]
Agent: "✅ Connected! I can see 1,234 leads. What would you like to analyze?"
```

**Implementation:**

1. Break down `ChatConnectorSetup` into conversation steps
2. Agent asks for one field at a time
3. Use `embeddedComponent: "secure-input"` for sensitive data
4. Provide real-time validation feedback
5. Keep setup state in conversation context

---

## Detailed Changes Required

### A. Message Type Enhancement

**File:** `apps/ui/src/components/AgentAssistant.tsx`

```typescript
interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "question";
  text: string;
  timestamp: number;
  thinkingSteps?: ThinkingStep[];
  
  // NEW: Embedded components for inline UI
  embeddedComponent?: 
    | "connector-selector" 
    | "data-uploader" 
    | "secure-input"
    | "connector-progress"
    | "data-preview";
  componentData?: any;
}
```

---

### B. Remove Modal States

**File:** `apps/ui/src/components/AgentAssistant.tsx`

```diff
- const [showConnectorMarketplace, setShowConnectorMarketplace] = useState(false);
- const [showConnectorSetup, setShowConnectorSetup] = useState(false);
- const [selectedConnectorForSetup, setSelectedConnectorForSetup] = useState<TenantConnector | null>(null);

+ // Connector state now managed in conversation messages
```

---

### C. LLM Function Calling Schema

**File:** `apps/ui/src/components/AgentAssistant.tsx`

```typescript
const AGENT_FUNCTION_TOOLS = [
  {
    type: "function",
    function: {
      name: "show_connector_options",
      description: "Display inline connector selection to user",
      parameters: {
        type: "object",
        properties: {
          connectors: {
            type: "array",
            items: { type: "string" },
            description: "List of suggested connector IDs (e.g., ['salesforce', 'stripe'])"
          },
          reason: {
            type: "string",
            description: "Why these connectors would help achieve the goal"
          }
        }
      }
    }
  },
  {
    type: "function",
    function: {
      name: "show_data_uploader",
      description: "Display inline file uploader to user",
      parameters: {
        type: "object",
        properties: {
          format: {
            type: "string",
            enum: ["csv", "excel", "json"],
            description: "Expected file format"
          },
          expectedColumns: {
            type: "array",
            items: { type: "string" },
            description: "Expected column names to guide user"
          }
        }
      }
    }
  }
];
```

---

### D. Inline Component Renderers

**New File:** `apps/ui/src/components/InlineConnectorSelector.tsx`

```typescript
interface InlineConnectorSelectorProps {
  connectors: string[];
  reason: string;
  onSelect: (connectorId: string) => void;
}

export function InlineConnectorSelector({ connectors, reason, onSelect }: InlineConnectorSelectorProps) {
  return (
    <div className="my-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
      <p className="mb-3 text-sm text-gray-700">{reason}</p>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {connectors.map(connector => (
          <button
            key={connector}
            onClick={() => onSelect(connector)}
            className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 hover:border-blue-400 hover:bg-blue-50"
          >
            <ConnectorIcon name={connector} />
            <span className="font-medium">{connector}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

**New File:** `apps/ui/src/components/InlineDataUploader.tsx`

```typescript
interface InlineDataUploaderProps {
  format: string;
  expectedColumns?: string[];
  onUploadComplete: (dataSource: DataSource) => void;
}

export function InlineDataUploader({ format, expectedColumns, onUploadComplete }: InlineDataUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  return (
    <div className="my-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
      {expectedColumns && (
        <p className="mb-2 text-xs text-gray-600">
          Expected columns: {expectedColumns.join(", ")}
        </p>
      )}
      
      <label className="flex cursor-pointer items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-white p-6 hover:border-blue-400">
        <input type="file" accept={`.${format}`} className="hidden" onChange={handleUpload} />
        <div className="text-center">
          <UploadIcon className="mx-auto mb-2 h-8 w-8 text-gray-400" />
          <span className="text-sm text-gray-600">
            Drop {format.toUpperCase()} file or click to browse
          </span>
        </div>
      </label>
      
      {uploading && (
        <div className="mt-3">
          <div className="h-2 rounded-full bg-gray-200">
            <div className="h-2 rounded-full bg-blue-500" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-1 text-xs text-gray-600">Uploading... {progress}%</p>
        </div>
      )}
    </div>
  );
}
```

---

### E. Message Renderer Update

**File:** `apps/ui/src/components/AgentAssistant.tsx`

```typescript
function renderMessage(message: Message) {
  return (
    <div className="message">
      <div className="message-text">{message.text}</div>
      
      {/* NEW: Render embedded components */}
      {message.embeddedComponent === "connector-selector" && (
        <InlineConnectorSelector
          connectors={message.componentData.connectors}
          reason={message.componentData.reason}
          onSelect={handleConnectorSelected}
        />
      )}
      
      {message.embeddedComponent === "data-uploader" && (
        <InlineDataUploader
          format={message.componentData.format}
          expectedColumns={message.componentData.expectedColumns}
          onUploadComplete={handleDataSourceAdded}
        />
      )}
      
      {message.embeddedComponent === "connector-progress" && (
        <InlineConnectorProgress
          connector={message.componentData.connectorName}
          status={message.componentData.status}
        />
      )}
    </div>
  );
}
```

---

### F. Updated handleSend() Flow

**File:** `apps/ui/src/components/AgentAssistant.tsx`

```typescript
const handleSend = async () => {
  // ... existing message handling ...
  
  try {
    const oaiResp = await postOpenAIChat({
      model: "dyocense-chat-mini",
      messages: [...messageHistory],
      temperature: 0.2,
      tools: AGENT_FUNCTION_TOOLS,  // NEW: Add function calling
      tool_choice: "auto",
      context: {
        ...buildEnhancedContext(),
        marketplace_opened: false,  // No longer needed
      },
    });
    
    const message = oaiResp.choices?.[0]?.message;
    
    // NEW: Handle function calls
    if (message?.tool_calls) {
      for (const toolCall of message.tool_calls) {
        if (toolCall.function.name === "show_connector_options") {
          const args = JSON.parse(toolCall.function.arguments);
          setMessages(m => [...m, {
            id: `connector-${Date.now()}`,
            role: "assistant",
            text: args.reason || "Here are some data sources you can connect:",
            embeddedComponent: "connector-selector",
            componentData: {
              connectors: args.connectors,
              reason: args.reason,
            },
            timestamp: Date.now(),
          }]);
        }
        
        if (toolCall.function.name === "show_data_uploader") {
          const args = JSON.parse(toolCall.function.arguments);
          setMessages(m => [...m, {
            id: `uploader-${Date.now()}`,
            role: "assistant",
            text: "Upload your data file here:",
            embeddedComponent: "data-uploader",
            componentData: {
              format: args.format,
              expectedColumns: args.expectedColumns,
            },
            timestamp: Date.now(),
          }]);
        }
      }
    }
    
    // Regular text response
    if (message?.content) {
      setMessages(m => [...m, {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text: message.content,
        timestamp: Date.now(),
      }]);
    }
  } catch (error) {
    // ... error handling ...
  }
};
```

---

### G. Remove Hardcoded Connector Detection

**File:** `apps/ui/src/components/AgentAssistant.tsx`

```diff
- // Check for connector-related keywords and optionally open the marketplace
- const connectorIntent = suggestConnectorFromIntent(userInput);
- if (connectorIntent && profile?.tenant_id) {
-   setShowConnectorMarketplace(true);
-   setMode("connectors");
- }

+ // LLM now decides via function calling when to suggest connectors
```

---

### H. Enhanced System Prompt

**File:** `apps/ui/src/components/AgentAssistant.tsx`

```typescript
const AGENT_SYSTEM_PROMPT = `You are a business operations AI assistant...

**Data Connection Guidelines:**
When users need data to accomplish their goals:

1. **Explain the need first**: "To forecast sales, I'll need historical sales data."

2. **Suggest specific options**:
   - If they have existing systems (CRM, ERP, etc.), suggest connectors
   - If they have spreadsheets, suggest file upload
   - Use function calling to show options inline

3. **Use these functions**:
   - \`show_connector_options(connectors, reason)\` - Display connector cards inline
   - \`show_data_uploader(format, expectedColumns)\` - Display upload widget inline

4. **Guide through setup conversationally**:
   - Ask for configuration details one at a time
   - Provide clear instructions for each step
   - Show progress and celebrate completion

5. **Never force data connections**:
   - Always explain WHY data is needed
   - Give users a choice to skip if they want to proceed without data
   - Offer to help with sample/demo data if they don't have their own

**Example Flow:**
User: "Help me optimize inventory"
You: "I can help! To give you accurate recommendations, I'll need inventory data. You can either:
     - Connect your existing inventory system (QuickBooks, SAP, etc.)
     - Upload a CSV file with your current stock levels
     
     Which would you prefer?"
[Use show_connector_options() or show_data_uploader() based on their choice]
`;
```

---

### I. Remove Modal JSX

**File:** `apps/ui/src/components/AgentAssistant.tsx`

```diff
- {showConnectorMarketplace && (
-   <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
-     <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
-       <div className="flex items-center justify-between p-6 border-b">
-         <h2 className="text-xl font-bold">Connect Data Source</h2>
-         <button onClick={() => { setShowConnectorMarketplace(false); setMode("chat"); }}>✕</button>
-       </div>
-       <div className="flex-1 overflow-y-auto">
-         <ConnectorMarketplace
-           onConnectorSelected={handleConnectorSelected}
-           tenantId={profile?.tenant_id || ""}
-         />
-       </div>
-     </div>
-   </div>
- )}

+ {/* Connectors now render inline in chat messages */}
```

---

## Benefits of This Approach

### 1. **Unified Conversational Experience**

- ✅ Everything happens in the chat stream
- ✅ Agent explains each step
- ✅ No jarring modal popups or mode switches

### 2. **LLM-Driven Intelligence**

- ✅ LLM decides WHEN to suggest data connections (not hardcoded keywords)
- ✅ LLM suggests WHICH connectors based on user's goal
- ✅ LLM provides contextual explanations

### 3. **Better User Guidance**

- ✅ Users understand WHY they need to connect data
- ✅ Clear explanations of what each connector does
- ✅ Step-by-step guidance through setup

### 4. **Flexible & Non-Intrusive**

- ✅ Users can skip data connections if desired
- ✅ Can continue conversation while setup happens
- ✅ No forced interruptions

### 5. **Consistent with Phase 1-3 Philosophy**

- ✅ Same pattern: remove hardcoded logic, make LLM-driven
- ✅ Keep everything conversational
- ✅ Rich context for intelligent decisions

---

## Migration Strategy

### Step 1: Add Inline Components (Non-Breaking)

- Create `InlineConnectorSelector` and `InlineDataUploader`
- Add `embeddedComponent` field to Message type
- Test rendering inline (while keeping modals as fallback)

### Step 2: Add Function Calling Support

- Add `AGENT_FUNCTION_TOOLS` schema
- Update `handleSend()` to parse function calls
- Test LLM triggering inline components

### Step 3: Update System Prompt

- Add data connection guidelines
- Train LLM to use function calling
- Test end-to-end flow

### Step 4: Remove Modals & Mode Switches

- Remove `showConnectorMarketplace` state
- Remove `mode === "data-upload"` logic
- Remove modal JSX
- Clean up unused code

### Step 5: Testing & Refinement

- Test with real user scenarios
- Refine prompts based on LLM behavior
- Add error handling for edge cases

---

## Example User Flows

### Flow 1: Sales Forecasting with CRM Connection

```
User: "I want to forecast sales for next quarter"

Agent: "I can help you forecast sales! To give accurate predictions, I'll need 
       historical sales data. Do you use a CRM system like Salesforce, HubSpot, 
       or Pipedrive?"

User: "Yes, we use Salesforce"

Agent: "Perfect! Let's connect your Salesforce account."
       [Inline connector card appears with Salesforce logo]

User: [clicks Salesforce card]

Agent: "Great! I need a few details:
       1. What's your Salesforce instance URL?"

User: "https://mycompany.salesforce.com"

Agent: "Got it! 2. Please provide your API key (it's secure)"
       [Secure input field appears inline]

User: [enters key]

Agent: "Testing connection... ✓ Connected! I can see:
       - 1,234 leads from the past 2 years
       - 487 closed deals
       - Average deal size: $15,000
       
       Ready to build your forecast. Would you like quarterly or monthly 
       predictions?"
```

### Flow 2: Inventory Optimization with CSV Upload

```
User: "Help me optimize inventory levels"

Agent: "I can help optimize your inventory! I'll need data about:
       - Current stock levels
       - Historical demand
       - Lead times from suppliers
       
       Do you have this in a spreadsheet, or is it in an inventory system?"

User: "I have it in Excel"

Agent: "Perfect! Upload your Excel file here. It should have columns like:
       product_name, current_stock, reorder_point, lead_time_days"
       [Inline uploader appears]

User: [uploads file]

Agent: "Uploading... 45%... 100% ✓ Done!
       
       Great! I can see:
       - 342 products
       - Stock levels ranging from 0 to 5,000 units
       - Average lead time: 14 days
       
       Let me analyze this... [thinking animation]
       
       ✓ Analysis complete! I found:
       - 23 products below optimal levels (risk of stockout)
       - 15 products overstocked (tying up $45K in capital)
       - 8 products with erratic demand patterns
       
       Would you like to see the detailed optimization plan?"
```

---

## Summary

**Current Problem:**

- Connectors and data uploads feel like separate apps
- Modal overlays break conversation flow
- No agent guidance or explanation
- Hardcoded keyword detection

**Proposed Solution:**

- Everything inline in the chat stream
- LLM-driven via function calling
- Conversational guidance at every step
- Smooth, uninterrupted experience

**Implementation:**

- Phase 1: Create inline components
- Phase 2: Add function calling support
- Phase 3: Update system prompt
- Phase 4: Remove modals and mode switches
- Phase 5: Testing and refinement

This approach maintains the same philosophy from Phases 1-3: **Keep everything conversational, LLM-driven, and context-aware.**
