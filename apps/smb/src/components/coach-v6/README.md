# Coach V6 - Fitness Dashboard Components

## Overview

Coach V6 represents a paradigm shift from "chat-first AI assistant" to **"Fitness Dashboard for Business Health"**.

**Mental Model**: "I'm checking my business health and getting coached" (like Whoop/Peloton) vs. "I'm talking to an AI" (like ChatGPT)

## Design Principles

1. **Dashboard-First** (not chat-first)
   - Business health score is the hero
   - Metrics are persistent and visible
   - Chat is secondary (via "Ask Coach" button)

2. **Proactive Coach** (not reactive)
   - AI generates recommendations automatically
   - Coach cards appear based on data patterns
   - User takes action on recommendations

3. **Fitness Metaphor** (not assistant metaphor)
   - Health score (0-100)
   - Progress tracking
   - Daily check-ins
   - Positive signals + areas to improve

4. **Action-Oriented** (not conversation-oriented)
   - Every recommendation has actionable steps
   - One-click actions (view invoices, create promotion, etc.)
   - Task completion tracking

## Components

### HealthScoreHeader

**Purpose**: Hero section showing business health score with critical alerts and positive signals.

**Props**:

- `score`: Current health score (0-100)
- `previousScore`: Previous score for trend calculation
- `trend`: 'up' | 'down' | 'stable'
- `changeAmount`: Numeric change from previous score
- `criticalAlerts`: Array of Alert objects
- `positiveSignals`: Array of Signal objects
- `onViewReport`: Callback for "View Report" button
- `onAskCoach`: Callback for "Ask Coach" button

**Features**:

- Gradient background based on score (red → yellow → blue → green)
- Sticky on scroll
- Expandable alerts/signals list
- Responsive design

---

### ProactiveCoachCard

**Purpose**: Display AI-generated recommendations with actionable steps.

**Props**:

- `recommendation`: CoachRecommendation object
- `onTakeAction`: Callback when action button clicked
- `onDismiss`: Callback when card dismissed

**Features**:

- Priority-based styling (critical/important/suggestion)
- Reasoning explanation
- Multiple action buttons
- Dismissible
- Timestamp display

---

### MetricsGrid

**Purpose**: Display 4 key business metrics with sparklines and trend indicators.

**Props**:

- `metrics`: Array of MetricSnapshot objects
- `onMetricClick`: Optional callback for metric drill-down

**Features**:

- 4-column grid (responsive: 1 col mobile, 2 col tablet, 4 col desktop)
- Inline sparklines (SVG)
- Trend icons (up/down/stable)
- Change percentage or absolute
- Hover effects

---

### GoalsColumn

**Purpose**: Display active goals with progress bars and due dates.

**Props**:

- `goals`: Array of GoalWithProgress objects
- `onGoalClick`: Optional callback for goal detail
- `onCreateGoal`: Optional callback for creating new goal

**Features**:

- Progress bars with color coding
- Status badges (on track / at risk / off track)
- Due date display
- Click to expand

---

### TasksColumn

**Purpose**: Display today's prioritized tasks with status indicators.

**Props**:

- `tasks`: Array of TaskWithPriority objects
- `onTaskClick`: Optional callback for task detail
- `onToggleComplete`: Optional callback for completing tasks

**Features**:

- Checkboxes for completion
- Priority badges (urgent / high / medium / low)
- Status indicators (todo / in progress / blocked / completed)
- Strike-through completed tasks
- Goal linkage badges

---

## Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  HEALTH SCORE HEADER (Sticky, Gradient Background)         │
│  Score: 78/100 | +3 from last week                         │
│  Critical Alerts | Positive Signals                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  METRICS GRID (4 columns)                                   │
│  Revenue | Cash Balance | Gross Margin | Active Orders     │
└─────────────────────────────────────────────────────────────┘

┌───────────────┬───────────────────────┬─────────────────────┐
│ COACH CARDS   │ GOALS & TASKS         │ EVIDENCE (Phase 2)  │
│               │                       │                     │
│ • Rec 1       │ Active Goals (3)      │ Recent activity     │
│ • Rec 2       │ • Goal 1 (78%)        │ Data sources        │
│ • Rec 3       │ • Goal 2 (30%)        │ Insights history    │
│               │                       │                     │
│               │ Today's Tasks (7)     │                     │
│               │ • Task 1 [Urgent]     │                     │
│               │ • Task 2 [High]       │                     │
│               │ • Task 3 [Medium]     │                     │
│               │                       │                     │
│ 360px         │ Flexible (1fr)        │ 360px               │
└───────────────┴───────────────────────┴─────────────────────┘
```

## Type Definitions

All types are defined in `types.ts`:

- **HealthScore**: Core health tracking with 4 weighted components
- **CoachRecommendation**: AI-generated recommendations with actions
- **Alert / Signal**: Health score header notifications
- **MetricSnapshot**: Key business metrics with sparklines
- **GoalWithProgress**: Goal tracking with progress bars
- **TaskWithPriority**: Task management with priority levels
- **Component Props**: All component prop interfaces
- **API Response Types**: Backend integration types
- **State Management**: CoachV6State interface

## Usage

```tsx
import { CoachV6 } from './pages/CoachV6';

// Add route in your app
<Route path="/coach/v6" element={<CoachV6 />} />
```

## Backend Integration (TODO)

### API Endpoints Needed

1. **GET /v1/tenants/{tenant_id}/health-score/trend**
   - Returns: HealthScoreTrendResponse
   - Includes: current score, previous score, components breakdown, trend data

2. **GET /v1/tenants/{tenant_id}/coach/recommendations**
   - Returns: CoachRecommendationsResponse
   - Includes: active recommendations, dismissed recommendations

3. **POST /v1/tenants/{tenant_id}/coach/recommendations/{rec_id}/dismiss**
   - Dismisses a recommendation

4. **GET /v1/tenants/{tenant_id}/metrics/snapshot**
   - Returns: Array of MetricSnapshot
   - Includes: Revenue, Cash Balance, Gross Margin, Active Orders

5. **GET /v1/tenants/{tenant_id}/goals**
   - Returns: Array of GoalWithProgress

6. **GET /v1/tenants/{tenant_id}/tasks/today**
   - Returns: Array of TaskWithPriority

### Daily Insights Job

- Runs at 6am local time per tenant
- Calculates health score
- Generates coach recommendations using GPT-4
- Uses templates in `packages/agent/coach_templates.py`

## Validation Sprint

This implementation is for **Week 1-2 Validation Sprint**.

### Goals

- 70%+ preference for V6 over V5
- 85%+ comprehension of health score
- 60%+ willing to pay $150-250/mo

### Testing

- 10 participants (SMB owners)
- 20-minute sessions
- Compare side-by-side with CoachV5
- See: `docs/validation/USER_TESTING_SCRIPT.md`

## Next Steps

1. **Week 1-2**: Validation sprint
2. **Go/No-Go Decision**: Based on validation results
3. **Phase 1** (Weeks 3-6): Full implementation if validated
   - Backend API endpoints
   - AI recommendation engine
   - WebSocket for real-time updates
   - Mobile responsive polish

## Design System

### Spacing

- Strict 4px/8px/12px/16px/20px/24px grid
- No inconsistent spacing (6px, 10px, 14px)

### Colors

- Health Score Gradient:
  - 86-100: Emerald gradient (excellent)
  - 76-85: Green gradient (good)
  - 61-75: Blue gradient (fair)
  - 41-60: Yellow gradient (needs attention)
  - 0-40: Red gradient (critical)

### Typography

- Headers: 600-700 weight
- Body: 400-500 weight
- Labels: UPPERCASE, 600 weight, 0.5px letter-spacing
- Numeric: Tabular nums for alignment

### Touch Targets

- Minimum 44px height for buttons
- Minimum 40px for interactive elements
- 16px icons in buttons (not 12-14px)

### Responsive Breakpoints

- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## Philosophy

> "We're not building a chatbot. We're building a fitness coach for your business."

The fitness analogy resonates because:

- SMB owners already track personal health (Whoop, Peloton, Apple Health)
- "Business health score" is intuitive
- Daily check-ins create habit
- Proactive coaching feels like a personal trainer
- Progress tracking motivates action

## Competitive Positioning

**"AI Business Fitness Coach"** - Category-defining positioning

Unlike:

- QuickBooks (accounting software)
- Gusto (payroll/HR)
- ChatGPT (general AI assistant)

We are:

- Proactive health monitoring
- Personalized coaching
- Action-oriented recommendations
- Fitness-inspired UX
