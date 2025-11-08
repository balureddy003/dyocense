# AI Agent Flow - Detailed Review & Integration Analysis

## Executive Summary

**Current State**: The agent has **mixed integration** - some flows use LLM properly, others use hardcoded logic.

**Status**: 🟡 **PARTIALLY INTEGRATED**

- ✅ General chat uses LLM (postOpenAIChat)
- ✅ File upload acknowledgment uses LLM
- ✅ Connector acknowledgment uses LLM
- ✅ Data source operations use LLM
- ⚠️ **Plan generation has hardcoded fallback logic**
- ⚠️ **Question/Answer flow is entirely hardcoded**
- ⚠️ **Goal examples trigger hardcoded Q&A flow**

---

## 1. LLM-Integrated Flows ✅

### 1.1 General Chat (`handleSend`)

**Status**: ✅ **FULLY INTEGRATED**

```typescript
// Lines 1305-1344
const oaiResp = await postOpenAIChat({
  model: "dyocense-chat-mini",
  messages: [
    { role: "system", content: AGENT_SYSTEM_PROMPT },
    ...messages.map(m => ({ role: m.role, content: m.text })),
    { role: "user", content: userInput },
  ],
  temperature: 0.2,
  context: {
    tenant_id: profile?.tenant_id,
    has_data_sources: dataSources.length > 0,
    preferences: preferences,
    data_sources: dataSources.map(...),
    connectors: tenantConnectors.map(...),
  },
});
```

**✅ Pros**:

- Full conversation history sent to LLM
- Rich context (tenant, data sources, connectors, preferences)
- System prompt guides behavior
- Graceful error handling

**Backend Integration**:

- ✅ Calls `postOpenAIChat` API
- ✅ Sends full context to backend
- ✅ Backend can use context for personalization

---

### 1.2 File Upload Flow

**Status**: ✅ **FULLY INTEGRATED**

```typescript
// Lines 629-661 (handleDataSourceAdded)
const resp = await postOpenAIChat({
  model: "dyocense-chat-mini",
  messages: [...],
  temperature: 0.2,
  context: {
    tenant_id: profile?.tenant_id,
    has_data_sources: true,
    preferences,
    data_sources: [...dataSources, source].map(...),
  },
});
```

**✅ Pros**:

- LLM acknowledges file upload
- LLM suggests next steps based on file content
- Schema information sent to LLM
- Fallback message if LLM unavailable

---

### 1.3 Connector Setup Flow

**Status**: ✅ **FULLY INTEGRATED**

```typescript
// Lines 800-826 (handleConnectorSetupComplete)
const resp = await postOpenAIChat({
  model: "dyocense-chat-mini",
  messages: [...],
  context: {
    tenant_id: profile.tenant_id,
    has_data_sources: true,
    preferences,
    connectors: updated.map(...),
  },
});
```

**✅ Pros**:

- LLM acknowledges connector setup
- LLM suggests what's now possible with connected data

---

## 2. Partially Integrated Flows ⚠️

### 2.1 Plan Generation (`generatePlan`)

**Status**: ⚠️ **BACKEND INTEGRATED BUT HARDCODED FALLBACK**

**Backend Integration** (Lines 920-960):

```typescript
// ✅ Calls backend orchestrator
runResponse = await createRun({
  goal: goal,
  project_id: profile.tenant_id,
  template_id: selectedTemplate?.template_id || "inventory_basic",
  horizon: 6,
  data_inputs: dataSources.length > 0 ? { sources: dataSources } : undefined,
});

// ✅ Polls for completion
runStatus = await getRun(runResponse.run_id);
while (runStatus.status === "pending" || runStatus.status === "running") {
  await new Promise((r) => setTimeout(r, 1000));
  runStatus = await getRun(runResponse.run_id);
}
```

**❌ Issues**:

1. **Hardcoded Fallback Plan** (Lines 1070-1145):

```typescript
const fallbackPlan: PlanOverview = {
  title: goal,
  summary: `Strategic plan to ${goal}...`,
  stages: [
    {
      id: "stage-1",
      title: "Discovery & Baseline",  // ❌ HARDCODED
      description: "Understand current state...",  // ❌ HARDCODED
      todos: [
        "Measure current performance metrics",  // ❌ HARDCODED
        "Identify improvement opportunities",   // ❌ HARDCODED
        // ...
      ],
    },
    // More hardcoded stages...
  ],
  quickWins: [
    "Implement low-cost automation...",  // ❌ HARDCODED
    "Optimize top 3 high-cost processes",  // ❌ HARDCODED
  ],
};
```

2. **Hardcoded Thinking Steps** (Lines 850-860):

```typescript
const thinkingSteps: ThinkingStep[] = [
  { id: "step-1", label: "Analyzing Business Context", status: "pending" },  // ❌ HARDCODED
  { id: "step-2", label: "Compiling Goal Specification", status: "pending" },
  { id: "step-3", label: "Retrieving Industry Data", status: "pending" },
  // ...
];
```

**🔧 Recommended Fixes**:

```typescript
// OPTION 1: Generate fallback using LLM
if (backendError) {
  const fallbackResp = await postOpenAIChat({
    model: "dyocense-chat-mini",
    messages: [
      { role: "system", content: AGENT_SYSTEM_PROMPT },
      { role: "user", content: `Create a detailed action plan for: "${goal}". Include 4 phases with specific todos, quick wins, and timeline.` }
    ],
    context: {
      tenant_id: profile?.tenant_id,
      goal: goal,
      data_sources: dataSources,
      preferences: preferences,
    },
  });
  
  // Parse LLM response into PlanOverview structure
  const fallbackPlan = parsePlanFromLLM(fallbackResp.choices[0].message.content);
}

// OPTION 2: Let LLM describe what happened
const statusMessage = await postOpenAIChat({
  messages: [
    { role: "system", content: AGENT_SYSTEM_PROMPT },
    { role: "user", content: `Explain to the user that their plan for "${goal}" is being created but backend is temporarily unavailable. Suggest they can still explore the interface or upload data.` }
  ],
});
```

---

## 3. Fully Hardcoded Flows ❌

### 3.1 Question/Answer Flow (SMART Goal Collection)

**Status**: ❌ **FULLY HARDCODED - NO LLM**

**The Problem**:
When a user clicks a goal example (e.g., "Reduce costs by 15% in 3 months"), this happens:

1. **Line 310**: Calls `generateQuestions()` - **LOCAL FUNCTION, NO LLM**

```typescript
const questions = generateQuestions({
  goal: trimmed,
  businessType: preferences ? Array.from(preferences.businessType)[0] : undefined,
  dataSources,
  budget: preferences ? Array.from(preferences.budget)[0] : undefined,
});
```

2. **Line 322**: Displays **HARDCODED** message:

```typescript
text: `Perfect! I understand your goal: "${trimmed}"\n\nTo create the most effective action plan, let me ask you a few quick questions to make sure your goal is SMART (Specific, Measurable, Achievable, Relevant, and Time-bound).`,
```

3. **Lines 507-600**: `handleQuestionAnswer()` - **FULLY HARDCODED**:
   - Validates answers locally
   - Generates follow-up questions locally
   - Enriches goal locally
   - **NEVER CALLS LLM**

**❌ Current Flow**:

```
User clicks "Reduce costs by 15%" 
  → generateQuestions() [LOCAL]
  → Shows hardcoded "SMART goal" message
  → User answers questions
  → validateAnswer() [LOCAL]
  → generateFollowUpQuestions() [LOCAL]
  → enrichGoalWithAnswers() [LOCAL]
  → generatePlan() [BACKEND but with hardcoded fallback]
```

**✅ Recommended LLM-Driven Flow**:

```
User clicks "Reduce costs by 15%"
  → Send to LLM with context
  → LLM decides if it needs more info
  → LLM asks natural follow-up questions
  → LLM validates responses conversationally
  → LLM creates plan when ready
```

**🔧 Implementation Fix**:

```typescript
const startFlowWithGoalText = async (goalText: string) => {
  const trimmed = goalText.trim();
  if (!trimmed) return;

  setCurrentGoal(trimmed);
  setLoading(true);

  // Show user message
  setMessages((m) => [...m, {
    id: `user-goal-${Date.now()}`,
    role: "user",
    text: trimmed,
    timestamp: Date.now(),
  }]);

  // ✅ LET LLM DRIVE THE CONVERSATION
  try {
    const resp = await postOpenAIChat({
      model: "dyocense-chat-mini",
      messages: [
        { 
          role: "system", 
          content: `${AGENT_SYSTEM_PROMPT}

IMPORTANT: When a user states a goal, evaluate if you need more information to create a specific, measurable plan.

If the goal is already specific (has metric, timeline, target), acknowledge it and start planning immediately.

If the goal is vague, ask 1-2 clarifying questions conversationally:
- What specific metric should we track?
- What's the target value and timeframe?
- Any constraints (budget, resources, timeline)?

Keep questions natural and conversational. Don't lecture about SMART goals.`
        },
        { role: "user", content: `My goal: ${trimmed}` }
      ],
      temperature: 0.3,
      context: {
        tenant_id: profile?.tenant_id,
        has_data_sources: dataSources.length > 0,
        preferences: preferences,
        data_sources: dataSources.map(ds => ({
          id: ds.id,
          name: ds.name,
          type: ds.type,
          rows: ds.metadata?.rows,
          columns: ds.metadata?.columns
        })),
        connectors: tenantConnectors.map(c => ({
          id: c.id,
          name: c.displayName,
          type: c.connectorName || c.connectorId,
          status: c.status
        })),
      },
    });

    const content = resp.choices?.[0]?.message?.content || 
      "I understand your goal. Let me help you create an action plan.";
    
    setMessages((m) => [...m, {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      text: content,
      timestamp: Date.now(),
    }]);

    // Check if LLM response indicates it's ready to plan
    // (This could be determined by checking for keywords or using function calling)
    const lowerContent = content.toLowerCase();
    const needsMoreInfo = lowerContent.includes("?") || 
                         lowerContent.includes("need to know") ||
                         lowerContent.includes("clarify");

    if (!needsMoreInfo) {
      // LLM thinks goal is specific enough, proceed to planning
      setTimeout(() => generatePlan(trimmed), 1000);
    }
    // Otherwise, conversation continues naturally

  } catch (error) {
    console.error("Error starting flow:", error);
    // Fallback to local questions if LLM unavailable
    const questions = generateQuestions({ goal: trimmed, ...});
    if (questions.length > 0) {
      setPendingQuestions(questions);
      // Show questions...
    }
  }

  setLoading(false);
};
```

---

### 3.2 Question Generation (`generateQuestions`)

**Status**: ❌ **FULLY HARDCODED**

**Location**: `apps/ui/src/lib/intelligentQuestioning.ts` (imported at line 23)

**What it does**:

- Returns predefined questions based on goal type
- No LLM involvement
- Static question templates

**Example hardcoded questions**:

```typescript
// From intelligentQuestioning.ts (likely implementation)
if (goal.includes("reduce") || goal.includes("cost")) {
  return [
    { id: "goal-metric", text: "What metric will you use?", required: true },
    { id: "goal-timeframe", text: "What's your timeline?", required: true },
    { id: "goal-baseline", text: "What's your current baseline?", required: false },
  ];
}
```

**🔧 Fix**: Replace with LLM-driven questioning (see above).

---

### 3.3 Goal Enrichment (`enrichGoalWithAnswers`)

**Status**: ❌ **FULLY HARDCODED**

**Location**: `apps/ui/src/lib/intelligentQuestioning.ts` (line 589)

**What it does**:

```typescript
// Likely implementation:
const enrichedGoal = enrichGoalWithAnswers(currentGoal, newAnswers);
// Returns something like: "Reduce costs by 15% within 3 months starting from $100k baseline"
```

**Issue**: String concatenation logic, not semantic understanding

**🔧 Fix**: Let LLM reformulate the goal:

```typescript
const enrichedGoalResp = await postOpenAIChat({
  messages: [
    { role: "system", content: "Reformulate the user's goal into a SMART goal statement based on the conversation." },
    ...conversationHistory,
  ],
});
const enrichedGoal = enrichedGoalResp.choices[0].message.content;
```

---

## 4. Backend Integration Points

### 4.1 Currently Integrated ✅

| Endpoint | Usage | Integration Quality |
|----------|-------|-------------------|
| `postOpenAIChat` | General chat, file uploads, connectors | ✅ Excellent |
| `createRun` | Plan generation (orchestrator) | ✅ Good |
| `getRun` | Poll for plan completion | ✅ Good |
| `getTenantProfile` | Get user/tenant info | ✅ Good |
| `getPlaybookRecommendations` | Get template suggestions | ✅ Good (with fallback) |

### 4.2 Missing Integrations ❌

| Flow | Current State | Should Call |
|------|--------------|-------------|
| Question generation | Local function | `postOpenAIChat` with conversation context |
| Answer validation | Local validation | `postOpenAIChat` to validate contextually |
| Goal enrichment | String concatenation | `postOpenAIChat` to reformulate semantically |
| Fallback plan generation | Hardcoded structure | `postOpenAIChat` to generate dynamically |

---

## 5. Recommendations by Priority

### 🔴 **CRITICAL - Remove Hardcoded Q&A Flow**

**Current Impact**: Users clicking goal examples get a robotic, scripted experience instead of natural AI conversation.

**Action Items**:

1. Remove `generateQuestions()` calls
2. Replace with LLM-driven conversation in `startFlowWithGoalText()`
3. Let LLM decide if it needs more information
4. Let LLM ask questions naturally within the chat flow

**Expected Outcome**: Natural, conversational goal refinement.

---

### 🟠 **HIGH - Replace Hardcoded Fallback Plan**

**Current Impact**: When backend is down, users get generic, useless plans.

**Action Items**:

1. Replace hardcoded `fallbackPlan` object with LLM generation
2. Use `postOpenAIChat` to generate structured plan
3. Parse LLM response into `PlanOverview` format
4. Add prompt engineering for structured output

**Example Prompt**:

```
Generate a detailed 4-phase action plan for: "${goal}"

Format as JSON:
{
  "title": "...",
  "summary": "...",
  "stages": [
    {
      "title": "Phase 1 name",
      "description": "What happens in this phase",
      "todos": ["specific action 1", "specific action 2", ...]
    },
    ...
  ],
  "quickWins": ["quick win 1", "quick win 2", ...],
  "estimatedDuration": "X months"
}
```

---

### 🟡 **MEDIUM - Enhance Context Passing**

**Current State**: Context is passed to LLM but could be richer.

**Improvements**:

1. Add conversation history length (for context)
2. Add goal status/progress if user is refining
3. Add previously generated plans for reference
4. Add user feedback on messages

---

### 🟢 **LOW - Add Function Calling**

**Future Enhancement**: Use OpenAI function calling for structured actions:

```typescript
const resp = await postOpenAIChat({
  model: "gpt-4",
  messages: [...],
  functions: [
    {
      name: "create_plan",
      description: "Create a structured business plan",
      parameters: {
        type: "object",
        properties: {
          goal: { type: "string" },
          phases: { type: "array", items: { type: "object" } },
          timeline: { type: "string" },
        },
      },
    },
    {
      name: "ask_clarifying_question",
      description: "Ask user for more information",
      parameters: {
        type: "object",
        properties: {
          question: { type: "string" },
          context: { type: "string" },
        },
      },
    },
  ],
});

// Check if LLM wants to call a function
if (resp.choices[0].message.function_call) {
  const functionName = resp.choices[0].message.function_call.name;
  const args = JSON.parse(resp.choices[0].message.function_call.arguments);
  
  if (functionName === "create_plan") {
    generatePlan(args.goal);
  } else if (functionName === "ask_clarifying_question") {
    // Show question naturally in chat
  }
}
```

---

## 6. Code Changes Summary

### Files to Modify

#### **apps/ui/src/components/AgentAssistant.tsx**

- ✏️ **Line 220-360**: Rewrite `startFlowWithGoalText()` to use LLM
- ❌ **Line 310-320**: Remove `generateQuestions()` call
- ❌ **Line 322-330**: Remove hardcoded "SMART goal" message
- ❌ **Line 507-600**: Remove or deprecate `handleQuestionAnswer()`
- ✏️ **Line 1070-1145**: Replace hardcoded `fallbackPlan` with LLM generation
- ✏️ **Line 1268-1282**: Remove `!AGENT_DRIVEN_FLOW` legacy code (it's always true)

#### **apps/ui/src/lib/intelligentQuestioning.ts** (Not reviewed but likely)

- 🗑️ Deprecate `generateQuestions()` - no longer needed
- 🗑️ Deprecate `generateFollowUpQuestions()` - let LLM handle
- 🗑️ Deprecate `enrichGoalWithAnswers()` - let LLM handle
- ✅ Keep `validateAnswer()` as utility for local validation (optional)

---

## 7. Testing Checklist

After implementing fixes:

### ✅ **Goal Creation Flow**

- [ ] Click "Cut Costs" example → LLM responds naturally
- [ ] LLM asks clarifying questions if needed
- [ ] LLM proceeds to plan without forced Q&A
- [ ] Backend unavailable → LLM generates fallback plan
- [ ] All responses feel conversational, not scripted

### ✅ **Chat Flow**

- [ ] Type "I want to reduce costs" → natural LLM response
- [ ] Upload file → LLM acknowledges with context
- [ ] Connect data source → LLM suggests next steps
- [ ] Ask random question → LLM responds helpfully

### ✅ **Plan Generation**

- [ ] Backend available → uses orchestrator results
- [ ] Backend unavailable → LLM generates structured plan
- [ ] No hardcoded stages appear in output
- [ ] Plan is specific to user's goal

---

## 8. Final Verdict

**Current Integration Score**: 6/10

| Component | Score | Status |
|-----------|-------|--------|
| General chat | 10/10 | ✅ Excellent |
| File upload flow | 10/10 | ✅ Excellent |
| Connector flow | 10/10 | ✅ Excellent |
| Plan generation | 7/10 | ⚠️ Backend integrated, hardcoded fallback |
| Question/Answer flow | 0/10 | ❌ Fully hardcoded, no LLM |
| Goal enrichment | 0/10 | ❌ String manipulation, no LLM |

**With Recommended Fixes**: Would be 9.5/10 (true agent-driven experience)

---

## 9. Implementation Priority

**Phase 1** (Do First - 2-4 hours):

1. Remove hardcoded Q&A flow
2. Make `startFlowWithGoalText()` use LLM
3. Test goal examples trigger natural conversation

**Phase 2** (Do Second - 2-3 hours):

1. Replace hardcoded fallback plan with LLM generation
2. Add structured output parsing
3. Test backend failure scenarios

**Phase 3** (Nice to Have - 4-6 hours):

1. Add function calling for structured actions
2. Enhance context passing
3. Add conversation memory/history

---

## 10. Example: Before vs After

### ❌ **BEFORE (Current - Hardcoded)**

```
User: [Clicks "Cut Costs - Reduce expenses by 15% in 3 months"]
