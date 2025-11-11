# Clear Flow: Goals → Coach → Action Plan

## Overview

Improved user flow with contextual guidance that connects Goals, AI Coach, and Action Plan pages seamlessly.

## The New Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. CREATE GOAL (Goals Page)                  │
│                                                                 │
│  User creates a goal (e.g., "Increase revenue by $50k")        │
│                                                                 │
│  ✅ Success Banner appears:                                     │
│  ┌────────────────────────────────────────────────────┐        │
│  │ Goal created! 🎉                                   │        │
│  │ Next step: Talk to your AI Coach to refine this   │        │
│  │ goal and create an action plan.                   │        │
│  │                                                     │        │
│  │         [Talk to AI Coach →]                       │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ User clicks "Talk to AI Coach"
                                │ (Sets sessionStorage flag)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  2. REFINE GOAL (Coach Page)                    │
│                                                                 │
│  🔵 Welcome Banner appears (from Goals):                        │
│  ┌────────────────────────────────────────────────────┐        │
│  │ Ready to refine your goal! 💪                      │        │
│  │ Ask your coach to break down your goal into steps, │        │
│  │ identify risks, or create a weekly action plan.   │        │
│  │                                                     │        │
│  │  [Break into steps]  [Create Action Plan →]       │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
│  User can:                                                      │
│  - Click "Break into steps" → Pre-fills chat input             │
│  - Click "Create Action Plan" → Goes to Planner                │
│  - Chat with coach to refine goal, discuss strategy            │
│                                                                 │
│  Three-Panel Layout:                                            │
│  ┌─────────┬──────────────┬──────────────┐                    │
│  │ Context │ Chat with AI │ Action Plan  │                    │
│  │ (Goals, │ Coach        │ Preview      │                    │
│  │  Tasks) │              │              │                    │
│  └─────────┴──────────────┴──────────────┘                    │
│                                                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ User clicks "Create Action Plan"
                                │ (Sets sessionStorage flag)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│               3. GENERATE PLAN (Planner Page)                   │
│                                                                 │
│  🔵 Welcome Banner appears (from Coach):                        │
│  ┌────────────────────────────────────────────────────┐        │
│  │ Ready to create your action plan! 📋              │        │
│  │ Your coach helped refine your goal. Now let's     │        │
│  │ turn it into a weekly action plan with specific   │        │
│  │ tasks.                                             │        │
│  │                                                     │        │
│  │         [Generate Action Plan]                     │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
│  User clicks "Generate Action Plan"                             │
│  → AI generates weekly tasks                                    │
│                                                                 │
│  ✅ Success Banner appears:                                     │
│  ┌────────────────────────────────────────────────────┐        │
│  │ Action plan created! 🎉                            │        │
│  │ Your weekly action plan is ready! Review the      │        │
│  │ tasks below. You can refine them with your AI     │        │
│  │ Coach anytime.                                     │        │
│  │                                                     │        │
│  │         [Refine with AI Coach →]                   │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
│  Plan Details:                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │ Increase Q1 Revenue                                │        │
│  │ 12 tasks | 0 assigned | 0 in motion                │        │
│  │ ▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0%           │        │
│  │                                                     │        │
│  │ Today's focus:                                     │        │
│  │ 01 Set up revenue tracking dashboard               │        │
│  │ 02 Review current pricing strategy                 │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ Optional: User can refine with coach
                                ▼
                       (Back to Coach Page)
```

## Flow Benefits

### 1. **Natural Progression**

- Goals → Coach → Action Plan follows the mental model of SMB users
- Each step builds on the previous one
- Clear "next step" guidance at each stage

### 2. **Contextual Banners**

- Banners appear ONLY when coming from another page in the flow
- Auto-dismiss after user acknowledges or takes action
- Uses sessionStorage to track flow state

### 3. **Flexible but Guided**

- Users can skip steps if they want (direct navigation still works)
- But the banners guide them through the optimal path
- Coach is central hub - can go back and forth

### 4. **Coach as Central Hub**

The AI Coach is positioned as the key interaction point:

- After creating goal → Go to coach to refine
- From coach → Generate action plan
- After plan created → Return to coach to refine tasks

## Technical Implementation

### Session Storage Flags

- `fromGoalsPage`: Set when navigating Goals → Coach
- `fromCoachPage`: Set when navigating Coach → Planner
- Flags are removed after banner is shown (one-time display)

### Banner States

#### Goals Page

```tsx
showSuccessBanner: boolean  // After creating a goal
```

#### Coach Page

```tsx
showWelcomeBanner: boolean  // When coming from Goals page
```

#### Planner Page

```tsx
showWelcomeBanner: boolean  // When coming from Coach page
showSuccessBanner: boolean  // After generating plan
```

### Navigation Handlers

**Goals → Coach:**

```tsx
onClick={() => {
    sessionStorage.setItem('fromGoalsPage', 'true')
    navigate('/coach')
}}
```

**Coach → Planner:**

```tsx
onClick={() => {
    sessionStorage.setItem('fromCoachPage', 'true')
    navigate('/planner')
}}
```

**Planner → Coach:**

```tsx
onClick={() => navigate('/coach')}
// No flag needed - coach is always welcoming
```

## User Journey Example

### Sarah, Small Restaurant Owner

**Step 1: Sets a Goal**

- Navigates to Goals page
- Clicks "Set your first goal"
- Types: "Increase weekly revenue by $2000"
- AI structures it into trackable goal
- Sees success banner: "Talk to AI Coach →"

**Step 2: Refines with Coach**

- Clicks button → Lands on Coach page
- Sees welcome banner: "Ready to refine your goal!"
- Clicks "Break into steps" OR chats with coach
- Coach suggests: Weekly specials, social media promos, loyalty program
- Clicks "Create Action Plan →"

**Step 3: Generates Action Plan**

- Lands on Planner page
- Sees welcome banner: "Ready to create your action plan!"
- Clicks "Generate Action Plan"
- AI creates 12 weekly tasks:
  - Week 1: Launch Tuesday special
  - Week 2: Start Instagram campaign
  - Week 3: Build loyalty program
  - etc.
- Sees success banner: "Action plan created! 🎉"
- Can click "Refine with AI Coach" to adjust tasks

**Step 4: Execution**

- Reviews weekly tasks in Planner
- Can refine with coach anytime
- Tracks progress in Analytics
- Coach monitors health score and suggests adjustments

## Comparison: Before vs After

### BEFORE (Direct to Planner)

```
Goals → Planner → Coach
❌ User confused: "What do I do with these tasks?"
❌ No context for plan generation
❌ Coach feels disconnected from goals
```

### AFTER (Coach in Middle)

```
Goals → Coach → Planner → Coach (refine)
✅ User understands: "Coach helps me break it down"
✅ Coach provides context and refinement
✅ Plan feels personalized and guided
✅ Circular flow: can always return to coach
```

## Key Improvements

1. **Coach is Central**: Positioned as the main interaction point, not an afterthought
2. **Contextual Guidance**: Banners appear only when relevant (not persistent clutter)
3. **Clear Next Steps**: Every banner explicitly states what comes next
4. **Flexible Flow**: Users can navigate freely, but guided path is clear
5. **SMB-Friendly Language**:
   - "Talk to AI Coach" (not "Open copilot")
   - "Refine your goal" (not "Optimize parameters")
   - "Weekly action plan" (not "Task decomposition")

## Analytics to Track

1. **Flow Completion Rate**: % of users who go Goals → Coach → Planner
2. **Banner Click-Through**: % who click CTAs in success/welcome banners
3. **Coach Engagement**: Time spent in coach after creating goal
4. **Plan Generation Time**: How long from goal creation to plan generation
5. **Return to Coach**: % who click "Refine with AI Coach" after plan creation

## Future Enhancements

1. **Onboarding Tour**: First-time users get guided tour through this flow
2. **Progress Indicator**: Subtle indicator showing "Goal ✓ → Coach → Plan"
3. **Smart Suggestions**: Coach proactively suggests creating plan when goal is refined
4. **Email Reminders**: "Your goal is waiting - talk to coach to create action plan"
5. **Weekly Check-ins**: Coach prompts user to review and adjust plan weekly
