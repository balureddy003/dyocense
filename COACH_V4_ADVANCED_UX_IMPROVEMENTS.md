# Coach V4 Advanced UX Improvements - Evidence & Reporting

**Date**: November 11, 2025  
**Focus**: Responsiveness, Evidence Display, Reporting, Backend Integration

---

## 🎯 Current State Analysis (From Screenshot)

### ✅ What's Working

- Today's Focus card with urgent tasks priority
- Traffic light health breakdown (Revenue: Green, Operations: Yellow, Customer: Red)
- "Fix This Now" action buttons
- Clean, professional UI
- Guided questions at bottom

### ⚠️ Missing Elements

1. **No evidence citations** - User can't verify AI claims
2. **No LangGraph run links** - Can't debug or audit reasoning
3. **Not mobile responsive** - Sidebar + main column doesn't adapt
4. **No data source indicators** - Which data was used?
5. **No confidence scores** - How sure is the AI?
6. **No export/share** - Can't share insights with team
7. **Missing visual charts** - Text-only health scores

---

## 💡 Advanced UX Improvements

### 1. **Evidence Citations** (Trust & Transparency)

**Problem**: "Customer churn 35%" - where did this come from?

**Solution**: Inline citations with expandable evidence

```tsx
Customer: 24/100 🚨 Critical
churn rate 35% (avg 15%) [📊 View Data]
   ↓ Click expands
┌─────────────────────────────────────┐
│ 📊 EVIDENCE                         │
│                                     │
│ Data Source: Stripe + CRM          │
│ Period: Oct 1-31, 2025             │
│ Sample Size: 142 customers         │
│                                     │
│ Churned: 50 customers (35%)        │
│ Industry Avg: 15% (Stripe Report)  │
│ Your Last Month: 28%               │
│                                     │
│ [📥 Export CSV] [🔗 View Raw Data] │
└─────────────────────────────────────┘
```

**Implementation**:

```tsx
metadata?: {
    evidence?: Array<{
        claim: string
        source: string
        data: any
        confidence: number
        timestamp: string
    }>
}
```

---

### 2. **LangGraph Run Inspection** (Developer-Friendly)

**Problem**: Can't audit AI reasoning steps

**Solution**: Collapsible "View Run" panel

```tsx
┌───────────────────────────────────────┐
│ Your health score is 35/100...        │
│                                       │
│ [🔍 View AI Reasoning]                │
│   ↓ Click expands                     │
│ ┌─────────────────────────────────┐  │
│ │ 🧠 LANGRAPH RUN                 │  │
│ │                                 │  │
│ │ Step 1: Data Collection ✓       │  │
│ │ ├─ Fetched health score         │  │
│ │ ├─ Fetched tasks (7 urgent)     │  │
│ │ └─ Fetched goals (2 active)     │  │
│ │                                 │  │
│ │ Step 2: Analysis ✓              │  │
│ │ ├─ Customer score: 24 (critical)│  │
│ │ └─ Priority: Fix churn first    │  │
│ │                                 │  │
│ │ Step 3: Response Generation ✓   │  │
│ │                                 │  │
│ │ Duration: 2.3s                  │  │
│ │ Cost: $0.004                    │  │
│ │ [🔗 Open Full Run]              │  │
│ └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

**Backend Integration**:

```typescript
// SSE response includes runUrl
{
    delta: "...",
    metadata: {
        runUrl: "https://langsmith.com/runs/abc123",
        steps: [
            { name: "data_collection", status: "complete", duration: 850 },
            { name: "analysis", status: "complete", duration: 1200 }
        ]
    }
}
```

---

### 3. **Mobile-First Responsive Design**

**Breakpoints**:

- Desktop: `>1024px` - Sidebar + Main
- Tablet: `768-1023px` - Collapsible sidebar
- Mobile: `<767px` - Full-screen, swipe for sidebar

**Mobile Layout**:

```
┌──────────────────┐
│ 🏢 Health: 35 ▼  │  ← Collapsible mini-dashboard
├──────────────────┤
│                  │
│ 🚨 Today's Focus │
│                  │
│ Customer 24/100  │
│ [Fix Now 🚀]     │
│                  │
├──────────────────┤
│ Message... 🎤 📩│  ← Voice + Send
└──────────────────┘
     ↓ Swipe up
┌──────────────────┐
│ 🎯 Active Goals  │  ← Bottom sheet
│ • Q4 Revenue     │
│ • Reduce Costs   │
└──────────────────┘
```

**Implementation**:

```tsx
import { useMediaQuery } from '@mantine/hooks'

const isMobile = useMediaQuery('(max-width: 767px)')
const isTablet = useMediaQuery('(max-width: 1023px)')

// Adaptive layout
{isMobile ? (
    <MobileCoachLayout />
) : (
    <DesktopCoachLayout />
)}
```

---

### 4. **Visual Health Charts** (Not Just Numbers)

**Problem**: "48/100" is abstract

**Solution**: Apple Watch-style rings + trend lines

```tsx
┌─────────────────────────────────────┐
│ 📊 BUSINESS HEALTH                  │
│                                     │
│    ╭─────╮                          │
│   ╱ 35  ╲    ↓ -13 from last week  │
│  │   🔴  │   (was 48)               │
│   ╲     ╱                           │
│    ╰─────╯                          │
│                                     │
│ Trend (30 days):                    │
│ 65 ──┐                              │
│      │     ╱╲                       │
│      └────╱  ╲___  ← You are here  │
│ 20 ──────────────╲                 │
│   Oct 1    15    31                │
│                                     │
│ 🟢 Revenue:   82 ████████░░         │
│ 🟡 Operations: 48 ████░░░░░         │
│ 🔴 Customer:   24 ██░░░░░░░         │
└─────────────────────────────────────┘
```

**Tech Stack**:

- **Recharts** or **Chart.js** for trend lines
- **SVG rings** for circular progress (like Apple Watch)
- Real-time data from `/v1/tenants/{id}/health-score/history`

---

### 5. **Confidence Indicators** (AI Transparency)

**Problem**: Is the AI guessing or certain?

**Solution**: Confidence badges

```tsx
Customer churn: 35%
[High Confidence 92%] ← Green badge

vs

Predicted churn next month: 40%
[Low Confidence 58%] ← Yellow badge
```

**Backend Response**:

```json
{
    "delta": "Customer churn is 35%",
    "metadata": {
        "evidence": [
            {
                "claim": "churn rate 35%",
                "confidence": 0.92,
                "source": "stripe_data",
                "sample_size": 142
            }
        ]
    }
}
```

---

### 6. **Export & Share Reports**

**Use Case**: Owner wants to share health report with co-founder

**Solution**: One-click export + shareable links

```tsx
┌─────────────────────────────────┐
│ Share This Report:              │
│                                 │
│ [📧 Email] [📱 SMS] [🔗 Link]  │
│                                 │
│ Export As:                      │
│ [📄 PDF] [📊 CSV] [📷 PNG]     │
│                                 │
│ Or copy shareable link:         │
│ dyocense.ai/r/abc123            │
│ ↳ Expires in 7 days             │
└─────────────────────────────────┘
```

**Backend**:

- `POST /v1/tenants/{id}/coach/reports/create`
- Returns shareable URL + PDF download link
- Embed snapshot of health, goals, recommendations

---

### 7. **Data Source Badges**

**Problem**: User doesn't know which data was analyzed

**Solution**: Inline badges + hover details

```tsx
┌───────────────────────────────────────┐
│ Revenue: 82/100 ✓                     │
│ [Stripe] [QuickBooks] [Google Ads]    │
│   ↓ Hover shows:                      │
│ ┌─────────────────────────────────┐   │
│ │ ✓ Stripe: $125K Oct revenue     │   │
│ │ ✓ QuickBooks: $8K expenses      │   │
│ │ ✓ Google Ads: 1,200 conversions │   │
│ │ Last synced: 2 hours ago        │   │
│ └─────────────────────────────────┘   │
└───────────────────────────────────────┘
```

**Implementation**:

```tsx
metadata?: {
    dataSources?: Array<{
        name: string
        icon: string
        lastSync: string
        recordCount: number
    }>
}
```

---

### 8. **Comparison View** (Benchmark Context)

**Problem**: "Is 35 health score good or bad?"

**Solution**: Industry benchmarks + peer comparison

```tsx
┌─────────────────────────────────────┐
│ YOUR HEALTH: 35/100                 │
│                                     │
│ vs Restaurants (your industry):     │
│ ┌─────────────────────────────┐    │
│ │ You        ●                │    │
│ │ Average      ●              │    │
│ │ Top 10%          ●          │    │
│ ├─────────────────────────────┤    │
│ │ 0   20   40   60   80   100 │    │
│ └─────────────────────────────┘    │
│                                     │
│ You're in the bottom 25% 📉        │
│                                     │
│ Similar businesses improved by:     │
│ • Reducing food waste (-$2K/mo)    │
│ • Optimizing labor costs (-15%)    │
│ • Running loyalty program (+22%)   │
│                                     │
│ [Show Me How]                       │
└─────────────────────────────────────┘
```

**Backend**:

- `/v1/tenants/{id}/benchmarks?industry=restaurant`
- Returns percentile, industry avg, top performers

---

### 9. **Progress Tracking** (Gamification)

**Problem**: No visibility into improvement over time

**Solution**: Fitness app-style progress tracking

```tsx
┌─────────────────────────────────────┐
│ 🏆 YOUR PROGRESS                    │
│                                     │
│ This Week:                          │
│ Health: 35 → 42 (+7) 🎉            │
│                                     │
│ Streak: 5 days checking in 🔥      │
│                                     │
│ Achievements Unlocked:              │
│ ✓ First Goal Created               │
│ ✓ Health Improved +5               │
│ ⭕ Get to 50 (In progress)         │
│                                     │
│ Keep going! You're on track to     │
│ reach 50 by Nov 18.                │
│                                     │
│ [Share Progress 📱]                 │
└─────────────────────────────────────┘
```

---

### 10. **Smart Notifications** (Re-engagement)

**Use Case**: User hasn't checked Coach in 3 days

**Solution**: Desktop + mobile push notifications

```
🚨 Your health score dropped to 32 (-6)

Customer churn spiked to 40%

[Open Coach] [Snooze]
```

**Implementation**:

- Browser Push API for desktop
- Integrate with backend `/v1/notifications/subscribe`
- Allow granular controls (urgent only, daily digest, etc.)

---

## 🔧 Technical Implementation Plan

### **Phase 1: Evidence & Transparency** (Week 1)

**Tasks**:

1. Extend Message interface with evidence metadata
2. Create `<EvidencePanel>` component with expandable citations
3. Add "View Run" button linking to LangGraph runUrl
4. Display data source badges on health metrics
5. Backend: Ensure SSE returns evidence array + runUrl

**Files**:

- `apps/smb/src/pages/CoachV4.tsx` - Add evidence rendering
- `apps/smb/src/components/EvidencePanel.tsx` - New component
- Backend: `/v1/tenants/{id}/coach/chat/stream` - Include evidence in metadata

---

### **Phase 2: Mobile Responsiveness** (Week 2)

**Tasks**:

1. Implement mobile breakpoints with `useMediaQuery`
2. Create `<MobileCoachLayout>` component
3. Add bottom sheet for goals/tasks on mobile
4. Voice input button for mobile users
5. Swipe gestures for sidebar (React Swipeable)

**Files**:

- `apps/smb/src/pages/CoachV4.tsx` - Responsive layouts
- `apps/smb/src/components/MobileCoachLayout.tsx` - New
- `apps/smb/src/components/BottomSheet.tsx` - New

---

### **Phase 3: Visual Charts & Reports** (Week 3)

**Tasks**:

1. Add Recharts for health trend lines
2. Create SVG circular progress rings (Apple Watch style)
3. Build export functionality (PDF, CSV, PNG)
4. Shareable report links
5. Backend: `/v1/tenants/{id}/health-score/history` endpoint

**Files**:

- `apps/smb/src/components/HealthChart.tsx` - New
- `apps/smb/src/components/CircularProgress.tsx` - New
- `apps/smb/src/components/ExportMenu.tsx` - New
- Backend: Report generation service

---

### **Phase 4: Benchmarks & Gamification** (Week 4)

**Tasks**:

1. Industry benchmark API integration
2. Progress tracking UI (streak, achievements)
3. Comparison charts (you vs industry)
4. Smart notifications setup
5. Backend: `/v1/tenants/{id}/benchmarks` + `/v1/progress`

**Files**:

- `apps/smb/src/components/BenchmarkChart.tsx` - New
- `apps/smb/src/components/ProgressTracker.tsx` - New
- `apps/smb/src/hooks/useNotifications.ts` - New

---

## 📋 Updated Message Interface

```typescript
interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: Date
    runUrl?: string
    isStreaming?: boolean
    metadata?: {
        intent?: string
        conversation_stage?: string
        focusTitle?: string
        quickActions?: Array<{ label: string; prompt: string }>
        
        // NEW: Evidence & Transparency
        evidence?: Array<{
            claim: string
            source: string  // 'stripe', 'quickbooks', etc.
            data: any
            confidence: number  // 0-1
            timestamp: string
            sampleSize?: number
        }>
        
        // NEW: LangGraph Run Details
        runSteps?: Array<{
            name: string
            status: 'complete' | 'running' | 'error'
            duration: number  // ms
            output?: any
        }>
        runCost?: number  // USD
        runDuration?: number  // ms
        
        // NEW: Data Sources Used
        dataSources?: Array<{
            name: string
            icon: string
            lastSync: string
            recordCount: number
        }>
        
        // NEW: Visual Data
        chartData?: {
            healthTrend?: Array<{ date: string; score: number }>
            categoryBreakdown?: { revenue: number; ops: number; customer: number }
        }
    }
}
```

---

## 🎨 Component Examples

### **EvidencePanel.tsx**

```typescript
interface EvidencePanelProps {
    evidence: Array<{
        claim: string
        source: string
        confidence: number
        data: any
    }>
}

export function EvidencePanel({ evidence }: EvidencePanelProps) {
    const [expanded, setExpanded] = useState(false)
    
    return (
        <div>
            <Button 
                size="xs" 
                variant="subtle"
                onClick={() => setExpanded(!expanded)}
            >
                📊 View Evidence ({evidence.length})
            </Button>
            
            {expanded && (
                <Card mt={8} withBorder>
                    <Stack gap={12}>
                        {evidence.map((e, i) => (
                            <div key={i}>
                                <Group gap={8}>
                                    <Badge 
                                        color={e.confidence > 0.8 ? 'green' : 'yellow'}
                                        size="sm"
                                    >
                                        {Math.round(e.confidence * 100)}% confident
                                    </Badge>
                                    <Text size="xs" c="dimmed">{e.source}</Text>
                                </Group>
                                <Text size="sm" mt={4}>{e.claim}</Text>
                                <Code block mt={4}>{JSON.stringify(e.data, null, 2)}</Code>
                            </div>
                        ))}
                    </Stack>
                </Card>
            )}
        </div>
    )
}
```

---

### **HealthTrendChart.tsx**

```typescript
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

interface HealthTrendChartProps {
    data: Array<{ date: string; score: number }>
}

export function HealthTrendChart({ data }: HealthTrendChartProps) {
    return (
        <ResponsiveContainer width="100%" height={150}>
            <LineChart data={data}>
                <XAxis 
                    dataKey="date" 
                    tickFormatter={(d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line 
                    type="monotone" 
                    dataKey="score" 
                    stroke="#8e44ad" 
                    strokeWidth={2}
                    dot={{ fill: '#8e44ad', r: 4 }}
                />
            </LineChart>
        </ResponsiveContainer>
    )
}
```

---

## 📱 Mobile-First CSS

```css
/* Responsive breakpoints */
@media (max-width: 767px) {
    .coach-sidebar {
        position: fixed;
        bottom: -100%;
        left: 0;
        right: 0;
        height: 60vh;
        transition: bottom 0.3s ease;
    }
    
    .coach-sidebar.open {
        bottom: 0;
    }
    
    .health-dashboard {
        padding: 12px;
        font-size: 14px;
    }
    
    .quick-actions {
        flex-direction: column;
        gap: 8px;
    }
}

@media (min-width: 768px) and (max-width: 1023px) {
    .coach-sidebar {
        width: 280px;
    }
}

@media (min-width: 1024px) {
    .coach-sidebar {
        width: 320px;
    }
}
```

---

## 🔌 Backend API Requirements

### **Enhanced SSE Response Format**

```typescript
// Streaming response chunks
{
    delta: "Your customer churn rate is 35%",
    metadata: {
        evidence: [
            {
                claim: "churn rate is 35%",
                source: "stripe",
                confidence: 0.92,
                data: {
                    total_customers: 142,
                    churned: 50,
                    churn_rate: 0.35,
                    period: "2025-10-01 to 2025-10-31"
                },
                timestamp: "2025-11-11T09:00:00Z"
            }
        ],
        dataSources: [
            { name: "Stripe", icon: "stripe", lastSync: "2 hours ago", recordCount: 142 },
            { name: "CRM", icon: "salesforce", lastSync: "1 day ago", recordCount: 450 }
        ],
        runSteps: [
            { name: "fetch_customer_data", status: "complete", duration: 850 },
            { name: "calculate_churn", status: "complete", duration: 120 }
        ]
    },
    done: false
}

// Final message
{
    delta: "",
    done: true,
    runUrl: "https://langsmith.com/runs/abc123def456",
    metadata: {
        runCost: 0.0042,
        runDuration: 2340,
        chartData: {
            healthTrend: [
                { date: "2025-10-01", score: 65 },
                { date: "2025-10-15", score: 52 },
                { date: "2025-10-31", score: 35 }
            ]
        }
    }
}
```

### **New Endpoints Needed**

```
GET  /v1/tenants/{id}/health-score/history?days=30
  → Returns trend data for charts

GET  /v1/tenants/{id}/benchmarks?industry=restaurant
  → Returns industry averages, percentiles

POST /v1/tenants/{id}/coach/reports/create
  → Generates shareable report, returns URL + PDF

GET  /v1/tenants/{id}/progress
  → Returns streak, achievements, milestones

POST /v1/notifications/subscribe
  → Subscribe to push notifications
```

---

## 🎯 Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Mobile Usage | Unknown | 40% | % of sessions from mobile |
| Evidence Click Rate | 0% | 25% | % who expand evidence panels |
| Export/Share Rate | 0% | 15% | % who export or share reports |
| Re-engagement (7d) | Unknown | 50% | % returning within 7 days |
| Trust Score (Survey) | Unknown | 8/10 | "How much do you trust Coach?" |

---

## 🚀 Quick Wins (Immediate Implementation)

**Week 1 Priorities**:

1. ✅ Add "View Run" link (if runUrl exists)
2. ✅ Show data source badges on health metrics
3. ✅ Mobile breakpoints for sidebar collapse
4. ✅ Add confidence badges to claims
5. ✅ Export button (even if just downloads JSON first)

**Code Example**:

```tsx
{m.runUrl && (
    <Button
        size="xs"
        variant="subtle"
        component="a"
        href={m.runUrl}
        target="_blank"
        leftSection={<IconExternalLink size={14} />}
    >
        🔍 View AI Run
    </Button>
)}
```

---

**This transforms Coach from a chat interface into a data-driven business intelligence platform with full transparency and mobile-first UX.**
