# Phase 1 Implementation Summary: LLM-Driven Goal Flow

**Date**: November 7, 2025  
**Status**: ✅ **COMPLETED**

## Overview

Successfully removed all hardcoded Q&A logic and replaced it with a fully LLM-driven conversational flow. Users now experience natural AI conversations instead of scripted question/answer sequences.

---

## Changes Made

### 1. Enhanced System Prompt ✅

**File**: `apps/ui/src/components/AgentAssistant.tsx` (Lines 33-53)

**What Changed**:

- Added "Goal Evaluation Guidelines" section to system prompt
- LLM now decides if goal is specific enough or needs clarification
- Instructions to ask 1-2 focused questions conversationally
- Guidance to avoid lecturing about SMART goals

**Before**:

```typescript
const AGENT_SYSTEM_PROMPT = `You are Dyocense's AI Business Assistant.
- Hold a natural conversation...
- Keep answers crisp.`;
```

**After**:

```typescript
const AGENT_SYSTEM_PROMPT = `You are Dyocense's AI Business Assistant.
...
**Goal Evaluation Guidelines:**
- When user states a goal, evaluate if it's specific enough.
- If goal has clear metric, target, timeframe → acknowledge and start planning
- If goal is vague → ask 1-2 focused questions conversationally
- Don't lecture about SMART goals - keep it natural`;
```

---

### 2. Rewrote startFlowWithGoalText() ✅

**File**: `apps/ui/src/components/AgentAssistant.tsx` (Lines 238-346)

**What Changed**:

- ❌ Removed `generateQuestions()` call (hardcoded logic)
- ❌ Removed hardcoded "SMART goal" message
- ❌ Removed simulated thinking steps
- ✅ Added `postOpenAIChat` call to LLM
- ✅ LLM analyzes goal and decides next steps
- ✅ Automatic plan generation if goal is specific
- ✅ Natural conversation if goal needs clarification

**Before** (Hardcoded):

```typescript
// Show thinking animation
setMessages([...thinkingSteps]);

// Generate hardcoded questions
const questions = generateQuestions({goal, ...});

if (questions.length > 0) {
  setMessages([
    "Perfect! To create SMART goal, let me ask questions...",
    questions[0]
  ]);
}
```

**After** (LLM-Driven):

```typescript
// Let LLM evaluate the goal
const resp = await postOpenAIChat({
  model: "dyocense-chat-mini",
  messages: [...conversationHistory, { role: "user", content: trimmed }],
  context: {
    tenant_id, goal, data_sources, connectors, preferences
  },
});

// LLM response is shown to user
setMessages([..., { role: "assistant", text: content }]);

// Analyze if LLM wants to plan or needs more info
if (!needsMoreInfo && shouldPlan) {
  generatePlan(trimmed);
}
// Otherwise conversation continues naturally
```

**Key Improvements**:

1. **Context-Aware**: LLM sees all tenant data, preferences, connectors
2. **Adaptive**: LLM decides if goal is specific enough
3. **Natural**: No scripted questions, real conversation
4. **Graceful Fallback**: If LLM unavailable, still attempts planning

---

### 3. Removed Legacy Q&A Routing ✅

**File**: `apps/ui/src/components/AgentAssistant.tsx` (Lines 1254-1273)

**What Changed**:

- Removed `!AGENT_DRIVEN_FLOW` conditional block
- All messages now go through LLM
- No more routing to `handleQuestionAnswer()`

**Before**:

```typescript
if (!AGENT_DRIVEN_FLOW) {
  // Legacy: check if answering a question
  if (lastMessage.role === "question") {
    handleQuestionAnswer(lastMessage.question, userInput);
    return;
  }
  
  // Legacy: detect goal-like input
  if (isFirstMessage && looksLikeGoal) {
    await startFlowWithGoalText(userInput);
    return;
  }
}

// Modern flow below...
```

**After**:

```typescript
// Agent-driven flow: all messages go through LLM
const userMsg: Message = {
  id: `user-${Date.now()}`,
  role: "user",
  text: userInput,
  timestamp: Date.now(),
};
setMessages((m) => [...m, userMsg]);

// Process with LLM...
```

---

### 4. Deprecated handleQuestionAnswer() ✅

**File**: `apps/ui/src/components/AgentAssistant.tsx` (Lines 510-585)

**What Changed**:

- Commented out entire function with explanatory note
- Kept for reference during transition
- Can be removed completely in future cleanup

**Before**:

```typescript
const handleQuestionAnswer = (question: Question, answer: string) => {
  // 75 lines of hardcoded question validation,
  // follow-up generation, and goal enrichment
};
```

**After**:

```typescript
// DEPRECATED: Legacy Q&A handler - kept for reference but no longer used
// Now using LLM-driven conversational flow in startFlowWithGoalText
/*
const handleQuestionAnswer = (question: Question, answer: string) => {
  ...
};
*/
```

---

### 5. Removed Quick Reply Buttons ✅

**File**: `apps/ui/src/components/AgentAssistant.tsx` (Lines 1598-1615)

**What Changed**:

- Commented out hardcoded quick reply buttons
- These were only used with deprecated question flow
- Users now type natural responses

**Before**:

```tsx
{msg.question?.suggestedAnswers && (
  <div className="Quick replies">
    <button onClick={() => handleQuestionAnswer(msg.question, ans)}>
      {ans}
    </button>
  </div>
)}
```

**After**:

```tsx
{/* DEPRECATED: Quick Reply Buttons - No longer used with LLM-driven flow
...commented out...
*/}
```

---

## User Experience Changes

### ❌ Before (Hardcoded)

```
User: [Clicks "Reduce costs by 15% in 3 months"]

[Animated thinking dots]
