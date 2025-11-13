# Coach V6: Fitness Dashboard Design Specification

## Overview

Transformation from chat-first to fitness-first interface for Dyocense AI Business Coach.

**Design Philosophy:** "Show health, suggest actions, chat when needed" (not "chat to discover health")

---

## Design Mockup Requirements

### 1. Hero Health Score Section (Top, Always Visible)

```
┌────────────────────────────────────────────────────────────────┐
│  TODAY'S BUSINESS HEALTH                            Nov 13, 2025│
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  [●●●●●●●○○○] 67/100  ↓ 8 points from last week         │  │
│  │                                                           │  │
│  │  🔴 NEEDS ATTENTION (2)          ✅ DOING WELL (2)       │  │
│  │  • Cash flow: $8.2k due in 3d    • Sales: +15% vs last mo│  │
│  │  • Inventory: 12 items aging     • Retention: 78% (+5%)  │  │
│  │                                                           │  │
│  │  [View Health Report] [💬 Ask Coach About This]         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

**Specifications:**

- Height: 160px (fixed)
- Background: Gradient based on score (Red<50, Yellow 50-70, Green>70)
- Score: 48px font, bold
- Trend arrow: 24px, with change amount
- Issues grid: 2 columns, 4 items max visible
- Sticky on scroll

---

### 2. Coach Recommendation Cards (Priority Order)

```
┌────────────────────────────────────────────────────────────────┐
│  🚨 URGENT: Cash Flow Risk                          [Dismiss ×]│
│                                                                  │
│  You have $8,200 due to vendors in 3 days, but only $6,400     │
│  in your checking account. Here's what I recommend:            │
│                                                                  │
│  1. 📞 Contact ABC Wholesale to extend payment 7 days          │
│  2. 📧 Follow up on 5 overdue customer invoices ($3,200)       │
│  3. 💰 Consider using line of credit for $2k short-term        │
│                                                                  │
│  [Create Action Plan] [Show Details] [Not Now]                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  💡 OPPORTUNITY: Inventory Optimization         [Dismiss ×]    │
│                                                                  │
│  12 items haven't sold in 90+ days, tying up $4,300.           │
│  Clearance sale could free up cash for faster movers.          │
│                                                                  │
│  [See Items] [Create Discount Plan] [Learn More]               │
└────────────────────────────────────────────────────────────────┘
```

**Specifications:**

- Card types: Critical (red), Important (yellow), Suggestion (blue)
- Max 3 cards visible at once
- Dismissible (slides out animation)
- Actions: Primary CTA button + secondary links
- Refresh every 4 hours or on user action completion

---

### 3. Unified Goals + Tasks View (Side by Side)

```
┌─────────────────────────┐  ┌──────────────────────────────────┐
│  🎯 ACTIVE GOALS (3)   │  │  📋 TODAY'S PRIORITIES (5)       │
│                         │  │                                   │
│  ✅ Reduce Costs       │  │  ☐ Review aging inventory        │
│     Target: -$5k/mo    │  │     Due today  🔴                │
│     Progress: 78%      │  │                                   │
│     [Mini graph]       │  │  ☐ Pay ABC Wholesale invoice     │
│                         │  │     Due in 3 days  🟡            │
│  🔄 Grow Revenue       │  │                                   │
│     Target: +$10k/mo   │  │  ☐ Follow up: 5 overdue invoices│
│     Progress: 34%      │  │     From coach rec  ✨           │
│     [Mini graph]       │  │                                   │
│                         │  │  ☐ Order supplies for weekend   │
│  📅 Hire Assistant     │  │     Scheduled  📅                │
│     Status: Planning   │  │                                   │
│     0 tasks created    │  │  ☐ Review daily sales report    │
│                         │  │     Routine  🔁                  │
│  [+ New Goal]          │  │                                   │
│                         │  │  [+ Add Task]  [View All (18)]  │
└─────────────────────────┘  └──────────────────────────────────┘
```

**Specifications:**

- Equal width columns (flex: 1 each)
- Goals: Show top 3 active, sorted by urgency
- Tasks: Show today + overdue, max 5 visible
- Visual indicators: emoji + color badges for priority
- Expandable on click for full details

---

### 4. Metrics Snapshot (Quick Glance)

```
┌────────────────────────────────────────────────────────────────┐
│  📊 KEY METRICS                                    Last 7 days │
│                                                                  │
│  Revenue        Expenses      Cash Flow     Customers          │
│  $24,300 ↑12%  $18,200 ↓3%   $6,100 ↑89%   347 ↑5%           │
│  [───▄▆█]      [█▆▄──]       [──▁▃█]       [▂▃▅▆█]           │
└────────────────────────────────────────────────────────────────┘
```

**Specifications:**

- Height: 100px
- 4 metrics in grid
- Sparkline charts (24px height)
- Trend arrows with percentage
- Click to expand detailed view

---

### 5. Chat Interface (Bottom/Supplemental)

```
┌────────────────────────────────────────────────────────────────┐
│  💬 Need help? Ask your business coach anything...             │
│  ─────────────────────────────────────────────────────────────│
│                                                                  │
│  [Type your question here...]                          [Send]  │
│                                                                  │
│  Quick asks:  [Revenue trends?] [Create weekly plan] [Help]   │
└────────────────────────────────────────────────────────────────┘
```

**Specifications:**

- Collapsible (expand when clicked)
- When expanded: Full chat history scrolls up
- Quick action buttons: Contextual to current page state
- Input: 40px height collapsed, expands to 120px when typing

---

## Color System (Fitness-Inspired)

### Health Score Colors

- **Critical (0-40):** `#EF4444` (Red 500)
- **Warning (41-60):** `#F59E0B` (Amber 500)
- **Fair (61-75):** `#3B82F6` (Blue 500)
- **Good (76-85):** `#10B981` (Emerald 500)
- **Excellent (86-100):** `#059669` (Emerald 600)

### Priority Colors

- **Urgent:** `#DC2626` (Red 600)
- **Important:** `#F59E0B` (Amber 500)
- **Suggestion:** `#3B82F6` (Blue 500)
- **Success:** `#059669` (Emerald 600)

### Spacing System (Strict)

- **xs:** 4px
- **sm:** 8px
- **md:** 12px
- **lg:** 16px
- **xl:** 24px
- **2xl:** 32px

---

## Responsive Breakpoints

### Desktop (1280px+)

```
[Health Score Header - Full Width]
[Coach Cards - Full Width]
[Goals (350px) | Tasks (flex) | Metrics (350px)]
[Chat - Collapsible Bar]
```

### Tablet (768px - 1279px)

```
[Health Score Header - Full Width]
[Coach Cards - Full Width]
[Goals & Tasks - Full Width, Stacked]
[Metrics - Full Width]
[Chat - Collapsible Bar]
```

### Mobile (< 768px)

```
[Health Score - Compact (80px height)]
[Coach Cards - Carousel (swipe)]
[Tabs: Goals | Tasks | Metrics]
[Chat - Bottom Sheet]
```

---

## User Interaction Flows

### Flow 1: Morning Check-in

1. User opens app
2. Sees health score: 67 (↓8)
3. Immediately sees "NEEDS ATTENTION: Cash flow risk"
4. Clicks "Create Action Plan"
5. Coach generates 3-step plan with tasks
6. User clicks "Add to Today's Tasks"
7. Tasks appear in right column with 🔴 urgent flag

**Time to Action: 15 seconds** (vs. 90+ seconds in current chat flow)

### Flow 2: Proactive Alert

1. 2pm: New coach card appears (animated slide-in)
2. "💡 Sales are 20% higher today vs. usual Tuesday"
3. "Consider ordering extra inventory for weekend"
4. User clicks "Show Recommendation"
5. See suggested items with quantities
6. Click "Create Order Task" → adds to task list

**Time to Action: 10 seconds** (current: user must ask first)

### Flow 3: Goal Progress Celebration

1. User completes task from goal
2. Goal progress bar animates: 67% → 72%
3. Confetti animation 🎉
4. Toast: "You're 72% toward Reduce Costs goal!"
5. Coach card: "Nice work! At this pace, you'll hit target in 12 days"

**Engagement: Positive reinforcement** (current: no celebration)

---

## Animation & Motion Principles

### Micro-interactions

- **Health score change:** Number counts up/down over 0.5s
- **Card dismiss:** Slide right + fade out (0.3s)
- **Task complete:** Checkbox → Strikethrough → Fade (0.4s)
- **New alert:** Slide down from top (0.5s ease-out)

### Loading States

- **Health score:** Skeleton with shimmer
- **Coach cards:** Pulse animation
- **Metrics:** Progressive reveal (left to right)

### Transitions

- **Page load:** Stagger children (0.05s delay each)
- **Panel expand:** Height transition (0.3s ease-in-out)
- **Hover:** Scale 1.02 + shadow increase (0.2s)

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance

- Color contrast ratio: Minimum 4.5:1 for text
- Touch targets: Minimum 44x44px
- Keyboard navigation: All actions accessible via Tab
- Screen reader: Proper ARIA labels on all interactive elements

### Focus States

- Visible focus ring: 2px solid blue, 2px offset
- Skip to main content link
- Focus trap in modals

### Reduced Motion

- Respect `prefers-reduced-motion` media query
- Disable animations, show instant state changes

---

## Performance Targets

### Load Times

- Initial render: < 1s
- Health score fetch: < 500ms
- Coach recommendations: < 1s
- Metric charts: < 800ms

### Interactions

- Button click response: < 100ms
- Task toggle: < 150ms
- Panel expand: < 300ms

### Bundle Size

- Main JS bundle: < 200kb gzipped
- CSS bundle: < 50kb gzipped
- Total page weight: < 500kb

---

## A/B Test Variants

### Test 1: Health Score Prominence

- **Variant A:** Large (current design, 160px)
- **Variant B:** Compact (80px, expandable)
- **Metric:** Engagement with health score details

### Test 2: Coach Card Style

- **Variant A:** Urgent style (red border, bold)
- **Variant B:** Friendly style (soft colors, casual tone)
- **Metric:** Action completion rate

### Test 3: Chat Placement

- **Variant A:** Bottom bar (current design)
- **Variant B:** Floating button (bottom right)
- **Metric:** Chat usage frequency

---

## Open Questions for User Testing

1. **Do users understand "Business Health Score" immediately?**
   - Alternative: "Business Fitness Score"
   - Alternative: "Success Score"

2. **Are coach recommendations perceived as helpful or annoying?**
   - Test: Frequency (daily vs. real-time)
   - Test: Dismissibility (permanent vs. snooze)

3. **Do users want chat visible or hidden by default?**
   - Test: Always visible vs. collapsible vs. floating

4. **How many coach cards is too many?**
   - Test: 1 card vs. 3 cards vs. unlimited scroll

5. **Should goals and tasks be unified or separate?**
   - Test: Current side-by-side vs. tabs vs. single merged list

---

## Success Metrics for Validation

### Comprehension (Qualitative)

- Can users explain what health score means? (Target: 80%+)
- Do users identify top priority within 10 seconds? (Target: 90%+)
- Do users know where to take action? (Target: 85%+)

### Preference (Qualitative)

- Prefer fitness dashboard vs. current chat? (Target: 70%+)
- Feel more in control of business? (Target: 75%+)
- Would pay premium for this ($200/mo vs $75)? (Target: 60%+)

### Behavior (In Prototype)

- Click through rate on coach recommendations (Target: 40%+)
- Time to complete first action (Target: <30 seconds)
- Return to view health score (Target: 2+ times per session)

---

## Next Steps After Design Approval

1. **Figma Mockups:** Full design system with components
2. **Clickable Prototype:** InVision or Figma prototype for testing
3. **User Testing:** 10 SMB owners, 30-min sessions each
4. **Analysis:** Compile findings and recommend go/no-go
5. **Refinement:** Iterate based on feedback (1 week)
6. **Engineering Handoff:** Detailed specs with Zeplin/Figma inspect

---

**Estimated Timeline:**

- Design mockups: 3 days
- User recruitment: 2 days (parallel)
- User testing: 5 days (2 sessions per day)
- Analysis & iteration: 2 days
- **Total: 12 days** (under 2-week target)

**Budget Estimate:**

- Design: 24 hours @ $150/hr = $3,600
- User recruitment: $1,500 (incentives: $100/participant)
- Analysis: 16 hours @ $150/hr = $2,400
- **Total: $7,500**

ROI if validated: Potential 3x pricing ($200 vs $75/mo) = $125/user/mo increase × 1000 users = **$125k/mo additional revenue**
