# Narrative Flow Gap Analysis

## Executive Summary

The application has **5 disconnected experiences**: Dashboard, Goals, Planner, Coach, and Analytics. Each page works independently but lacks a cohesive narrative that guides users through their business improvement journey.

## Current State: Gap Analysis

### 1. **Dashboard (Home.tsx)** - The Starting Point

**What It Shows:**

- Health Score: 75/100 with trend
- Daily Metrics: Revenue, Orders, Fill Rate, Rating
- Active Goals progress
- Multi-Horizon Planner (Daily/Weekly/Quarterly/Yearly tasks)
- AI Coach Insights (2 static alerts)
- Streak Counter

**Critical Gaps:**
❌ **No actionable next steps** - User sees health score 75/100 but no guidance on "what to do about it"
❌ **Insights are static mock data** - Not connected to actual health breakdown (revenue: 80, ops: 70, customer: 75)
❌ **No path to Goals page** - User sees goals but can't easily create new ones from insights
❌ **No Coach integration** - Quick questions like "Why is my ops score 70?" don't flow naturally
❌ **Analytics disconnected** - No link to "See trends" or "Analyze this metric"

### 2. **Goals Page** - Goal Management

**What It Shows:**

- Active goals with progress bars
- AI-powered goal generation from natural language
- Goal tracking with milestones (25%, 50%, 75%, 100%)

**Critical Gaps:**
❌ **No context from Dashboard** - Doesn't know user came from health score 75/100 with ops: 70
❌ **No suggested goals** - Should suggest "Improve operations health" based on dashboard data
❌ **Milestone celebrations isolated** - Achievements don't flow back to Dashboard or Analytics
❌ **No task generation** - Goals don't auto-create tasks for Planner

### 3. **Planner Page** - Action Plans

**What It Shows:**

- Current plan with tasks
- Task assignments and status
- Progress stats (total, assigned, in motion)

**Critical Gaps:**
❌ **No connection to Goals** - Tasks aren't linked to specific goals
❌ **No AI suggestions** - Doesn't use health breakdown to suggest focus areas
❌ **Horizon confusion** - Has multi-horizon concept but not clear how it relates to goals
❌ **No Coach integration** - Can't ask "Help me prioritize these tasks"

### 4. **Coach Page** - AI Assistant

**What It Shows:**

- Chat interface with AI Business Coach
- Quick action prompts
- Conversation history

**Critical Gaps:**
❌ **No context awareness** - Doesn't know user's health score, active goals, or pending tasks
❌ **Generic responses** - Fixed after our update, but still needs contextual suggestions
❌ **No action follow-through** - Can discuss goals but can't create them from chat
❌ **Isolated from journey** - Should be the connective tissue between all pages

### 5. **Analytics Page** - Progress Tracking

**What It Shows:**

- Health score trends over time
- Goal progress visualization
- Task completion heatmap
- Revenue breakdown

**Critical Gaps:**
❌ **No insights generated** - Just shows data, doesn't explain "why"
❌ **No Coach integration** - Can't ask "Why did my score drop in week 3?"
❌ **No goal suggestions** - Seeing declining trend should prompt "Set a recovery goal"
❌ **No action items** - User sees problems but no path to fixing them

## The Missing Narrative Thread

### What Should Happen (Ideal User Journey)

```
Day 1: DISCOVER
Dashboard → Health Score 75/100
  → "Operations health is 70/100" (RED FLAG)
  → AI Insight: "Your inventory turnover is 18% below target"
  → CTA: "Ask Coach why" | "Create improvement goal" | "See analytics"

Day 1: UNDERSTAND  
Coach → Ask "Why is my operations health low?"
  → Coach: "Based on your 720 orders and 20 inventory items, I see:
     - 14% of items are low-stock
     - Average stock-out duration: 3.2 days
     - This is costing you ~$1,200/week in lost sales"
  → CTA: "Set a goal to improve this" | "Show me the data"

Day 1: PLAN
Goals → Prompted: "Improve Inventory Health to 85/100"
  → Auto-suggests: Target 95% in-stock rate by end of quarter
  → CTA: "Generate action plan"

Day 1: EXECUTE
Planner → Auto-generated tasks:
  WEEKLY: "Review low-stock alerts daily"
  WEEKLY: "Set reorder points for top 10 SKUs"  
  QUARTERLY: "Implement automated reorder system"
  → Each task linked to goal "Improve Inventory Health"
  → CTA: "Get Coach help on task" | "Track in Analytics"

Day 30: MONITOR
Analytics → Shows operations health trend 70 → 73 → 78 → 82
  → Goal progress: 60% toward 95% in-stock target
  → AI Insight: "Great progress! Stock-outs reduced by 40%"
  → CTA: "Celebrate milestone" | "Ask Coach for next steps"

Day 30: OPTIMIZE
Coach → Proactive: "You're 60% to your inventory goal! Ready to tackle the next area?"
  → Suggests: "Customer health is 75/100. Want to improve retention?"
  → User: "Yes, create a goal"
  → Coach: Creates goal + tasks, journey repeats
```

### What Actually Happens (Current Experience)

```
User opens Dashboard → Sees health 75/100 → "OK, I guess?"
User sees goals → "I have 2 goals... are they related to my health score?"
User checks Analytics → "My score went up... why?"
User asks Coach → "Help me improve" → Gets generic advice
User closes app → No clear next action
```

## Root Causes

### 1. **Data Silos**

Each page fetches its own data independently:

- Dashboard: Gets health score + goals + tasks
- Goals: Gets goals only
- Analytics: Gets analytics data only
- Coach: Gets nothing (just chat history)
- Planner: Gets plans only

**Solution Needed:** Shared context provider with:

```typescript
{
  healthScore: { overall: 75, revenue: 80, operations: 70, customer: 75 },
  insights: ["Ops 70/100: Inventory issues", "Customer 75/100: Retention opportunity"],
  activeGoals: [...],
  pendingTasks: { daily: [...], weekly: [...] },
  recentActivity: [...],
  focusArea: "operations" // Derived from lowest health dimension
}
```

### 2. **No Cross-Page Navigation Prompts**

Components don't know about each other:

- Health score component doesn't link to Analytics or Coach
- Goal progress doesn't link to Planner or Coach
- Insights don't link to Goals or Coach
- Coach can't create goals/tasks

**Solution Needed:** Contextual CTAs everywhere:

```tsx
<HealthScore score={75} />
  → {breakdown.operations < 80 && (
    <Alert>
      Operations health needs attention
      <Button onClick={() => navigate('/coach?q=improve-operations')}>
        Ask Coach
      </Button>
      <Button onClick={() => navigate('/goals?suggest=operations')}>
        Set Goal
      </Button>
    </Alert>
  )}
```

### 3. **Coach Not Integrated**

Coach is isolated from the data ecosystem:

- Can't see current health scores
- Can't see active goals
- Can't create goals or tasks from conversation
- Can't reference specific analytics

**Solution Needed:** Coach context awareness:

```typescript
// When user asks "Why is my health score low?"
coachContext = {
  healthScore: 75,
  breakdown: { ops: 70, ... },
  goals: [{ title: "Revenue growth", progress: 45% }],
  tasks: [{ title: "Review inventory", status: "overdue" }],
  insights: ["14% items low-stock"]
}
// Coach uses this to give specific answers
```

### 4. **No AI-Driven Suggestions**

System has data but doesn't generate insights:

- Health score 70 in operations → Should suggest "Focus on inventory"
- Goal 45% complete with 10 days left → Should warn "Off track, need help?"
- Task overdue → Should ask "Need to break this down?"

**Solution Needed:** Proactive AI insights engine:

```typescript
generateInsights(context) {
  const insights = []
  
  // Low health dimension
  if (context.healthScore.operations < 75) {
    insights.push({
      type: 'alert',
      message: 'Operations health needs attention (70/100)',
      actions: [
        { label: 'Ask Coach why', link: '/coach?q=ops-health' },
        { label: 'Create goal', link: '/goals?suggest=ops' }
      ]
    })
  }
  
  // Off-track goal
  const offTrackGoals = context.goals.filter(g => 
    g.daysRemaining < 30 && g.progress < 50
  )
  if (offTrackGoals.length > 0) {
    insights.push({
      type: 'alert',
      message: `${offTrackGoals.length} goals may be off-track`,
      actions: [
        { label: 'Get help', link: '/coach?q=goal-progress' },
        { label: 'Adjust timeline', link: '/goals' }
      ]
    })
  }
  
  return insights
}
```

### 5. **No Feedback Loop**

User actions don't close the loop:

- Complete a task → Health score should update
- Achieve goal milestone → Should celebrate + suggest next goal
- Ask Coach question → Should log as activity
- Health improves → Should acknowledge and reinforce

**Solution Needed:** Activity stream + score recalculation:

```typescript
onTaskComplete(task) {
  // 1. Update task status
  await updateTask(task.id, { status: 'completed' })
  
  // 2. Check goal progress
  const goal = task.linkedGoal
  const newProgress = calculateGoalProgress(goal)
  
  // 3. Recalculate health score
  const newHealth = await recalculateHealthScore(tenantId)
  
  // 4. Check for milestones
  if (newProgress >= 75 && oldProgress < 75) {
    celebrateMilestone(goal, 75)
    suggestNextAction()
  }
  
  // 5. Generate insight
  addInsight({
    type: 'success',
    message: `Great! Task "${task.title}" completed. ${goal.title} now ${newProgress}%`,
    actions: [
      { label: 'See progress', link: '/analytics' },
      { label: 'What\'s next?', link: '/coach' }
    ]
  })
}
```

## Implementation Priority

### Phase 1: Foundation (HIGH - Do First)

1. **Create Shared Context Provider** (`/apps/smb/src/contexts/BusinessContext.tsx`)
   - Health score with breakdown
   - Active goals with progress
   - Pending tasks by horizon
   - AI-generated insights
   - Focus area (lowest health dimension)

2. **Enhance Coach Context** (`/services/smb_gateway/multi_agent_coach.py`)
   - Already done: Pass business metrics to agents ✅
   - TODO: Add goal-aware responses
   - TODO: Add task-aware responses
   - TODO: Enable action triggers (create goal, create task)

### Phase 2: Connections (MEDIUM - Do Second)

3. **Add Cross-Page Navigation**
   - Dashboard insights → Coach/Goals/Analytics
   - Health score component → Detailed breakdown in Analytics
   - Goal progress → Ask Coach for help
   - Analytics trends → Create goal from insight

4. **Implement Insights Engine** (`/services/smb_gateway/insights_service.py`)
   - Analyze health breakdown → Generate alerts
   - Monitor goal progress → Flag off-track goals
   - Track task completion → Suggest optimizations
   - Detect patterns → Proactive suggestions

### Phase 3: Intelligence (NICE TO HAVE - Do Third)

5. **Add Coach Actions**
   - "Create goal" command in chat → Calls goals API
   - "Show me analytics" → Navigates with context
   - "Break down this task" → Creates subtasks

6. **Implement Feedback Loop**
   - Task completion → Health recalculation
   - Goal milestones → Celebrations + suggestions
   - Health improvements → Positive reinforcement

## Concrete Examples of Fixes

### Fix 1: Dashboard Insights Should Be Contextual

**Current (Static Mock):**

```tsx
const mockInsights = [
  {
    message: 'Cart abandonment rate is up 18%...',
    type: 'alert',
  }
]
```

**Fixed (Dynamic from Health Data):**

```tsx
const generateInsights = (healthScore, goals, tasks) => {
  const insights = []
  
  // Low operations health
  if (healthScore.breakdown.operations < 75) {
    insights.push({
      id: '1',
      message: `Operations health is ${healthScore.breakdown.operations}/100. Your inventory turnover is below target.`,
      type: 'alert',
      actions: [
        { label: 'Ask AI Coach', onClick: () => navigate('/coach?q=improve-operations') },
        { label: 'Set Improvement Goal', onClick: () => navigate('/goals?suggest=operations') }
      ]
    })
  }
  
  // Off-track goals
  const offTrack = goals.filter(g => 
    g.daysRemaining < 30 && (g.current / g.target) < 0.5
  )
  if (offTrack.length > 0) {
    insights.push({
      id: '2',
      message: `${offTrack.length} goals may be off-track. Goal "${offTrack[0].title}" is ${Math.round(offTrack[0].current/offTrack[0].target * 100)}% complete with ${offTrack[0].daysRemaining} days left.`,
      type: 'alert',
      actions: [
        { label: 'Get Coach Help', onClick: () => navigate('/coach?context=goal-' + offTrack[0].id) },
        { label: 'View Progress', onClick: () => navigate('/analytics') }
      ]
    })
  }
  
  return insights
}
```

### Fix 2: Health Score Should Link to Details

**Current:**

```tsx
<BusinessHealthScore score={75} trend={2} />
```

**Fixed:**

```tsx
<BusinessHealthScore 
  score={75} 
  trend={2}
  breakdown={{ revenue: 80, operations: 70, customer: 75 }}
  onClickBreakdown={() => navigate('/analytics?view=health-breakdown')}
  onClickImprove={(dimension) => navigate(`/coach?q=improve-${dimension}`)}
/>
```

### Fix 3: Goals Should Suggest Actions

**Current (Goals Page):**

```tsx
// Just shows goals list, no suggestions
```

**Fixed:**

```tsx
// On Goals page load, check for suggestions
useEffect(() => {
  const params = new URLSearchParams(location.search)
  const suggest = params.get('suggest')
  
  if (suggest === 'operations') {
    // Auto-populate goal creation with suggestion
    setGoalInput('Improve inventory turnover to reduce stock-outs by 50%')
    setShowCreateModal(true)
    handleGenerateGoal() // Auto-generate with AI
  }
}, [location])
```

### Fix 4: Coach Should Be Context-Aware

**Current:**

```tsx
// Coach just gets message history
const response = await post('/coach/chat', {
  message: userMessage,
  conversation_history: messages
})
```

**Fixed:**

```tsx
// Coach gets full business context
const response = await post('/coach/chat', {
  message: userMessage,
  conversation_history: messages,
  business_context: {
    health_score: healthScoreData,
    active_goals: goalsData,
    pending_tasks: tasksData,
    recent_insights: insightsData,
    focus_area: deriveFocusArea(healthScoreData) // 'operations' if lowest
  }
})

// And Coach can take actions
if (response.action === 'create_goal') {
  navigate('/goals', { 
    state: { 
      suggested: response.goal_template 
    } 
  })
}
```

### Fix 5: Analytics Should Generate Insights

**Current:**

```tsx
// Just shows charts, no interpretation
<LineChart data={healthScoreTrend} />
```

**Fixed:**

```tsx
<LineChart data={healthScoreTrend} />
<InsightCard
  insights={analyzeHealthTrend(healthScoreTrend)}
  // e.g., "Your health score dropped 5 points in Week 3, 
  //       coinciding with increased stock-outs"
  actions={[
    { label: 'Ask Coach Why', onClick: () => navigate('/coach?q=week3-drop') },
    { label: 'Prevent Recurrence', onClick: () => navigate('/goals?suggest=inventory-alerts') }
  ]}
/>
```

## Success Metrics

After implementing these fixes, users should:

1. **Understand Next Steps**
   - 90% of users know what action to take after viewing Dashboard

2. **Navigate with Purpose**
   - 70% of page transitions are through contextual CTAs (not menu)

3. **Use Coach Effectively**
   - 80% of Coach conversations reference specific business data
   - 50% of Coach conversations result in an action (goal/task creation)

4. **Close the Loop**
   - 60% of goals have linked tasks
   - 80% of task completions result in health score recalculation
   - 90% of milestones trigger celebrations

5. **Feel Progress**
   - 70% of users can articulate their focus area
   - 80% of users check Analytics after completing tasks
   - 60% of users create follow-up goals after achieving one

## Next Steps

1. **Review this analysis** - Confirm the gaps resonate with your vision
2. **Prioritize fixes** - Which phase to tackle first?
3. **Implement Shared Context** - Foundation for everything else
4. **Add Cross-Navigation** - Quick win for user experience
5. **Enhance Coach Context** - Make AI truly helpful

Would you like me to start implementing any of these fixes?
